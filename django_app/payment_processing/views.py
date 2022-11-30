import datetime
import logging
import os
import json
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, Http404
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
import stripe

from payment_processing.models import CreditCard, BankInfo, Receipt
from settings import (STRIPE_PUBLISHABLE, STRIPE_SECRET,
                      TOTAL_PURCHASE_VALUE_SUSPICIOUS,
                      INDIVIDUAL_PURCHASE_VALUE_SUSPICIOUS)
from media.models import Song, Album
from accounts.models import DownloadCharge, MediaDownload, Profile
from player.models import QueuedDownload

from utils import JSON, render_appropriately

import gangnam_client
from functools import reduce


logger = logging.getLogger(__name__)


@csrf_exempt
@login_required
def add_card(request):
    """
    Called from payment/add_card, expects POST input of the format
    stripe_id: string
    last4: string (of length 4)
    cardType: string (Visa, Mastercard)
    (all of the above are supplied by a call to stripe in the js)

    Output: JSON
    """
    data = {}
    if request.method == 'POST':
        stripe_id = request.POST.get('token', None)
        last4 = request.POST.get('last4', None)
        cardType = request.POST.get('cardType', None).replace(' ', '')
        if not (stripe_id and last4 and cardType):
            data['message'] = 'There was a problem adding your card.'
        else:
            stripe.api_key = STRIPE_SECRET
            # Stripe by default uses a card to create a single-use token. This
            # has been done in the js, and now we are using the generated token
            # to create a "customer," essentially a reusable card token.
            try:
                customer = stripe.Customer.create(card=stripe_id)
            except stripe.StripeError as e:
                data['message'] = 'There was a problem adding your card: ' \
                    + e.message
                customer = None
            if customer:
                new_card = CreditCard.objects.create(user=request.user,
                                                     stripe_id=customer.id,
                                                     last4=last4,
                                                     cardType=cardType)
                data['success'] = True
                data['message'] = 'Credit card added successfully.'
                data['card_pk'] = new_card.pk
                data['cardType'] = cardType
                data['digits'] = last4
    else:
        data['message'] = 'Improper request.'

    return JSON(data)


@csrf_exempt
@login_required
def remove_card(request):
    """
    Called from payment/remove_card, expects GET data
    delete: int (the pk of the card to delete)

    Output: JSON
    """
    delete = request.POST.get('delete', None)
    if delete:
        try:
            deleting = CreditCard.objects.get(pk=delete)
        except ObjectDoesNotExist:
            deleting = None
        if deleting and deleting.user == request.user:
            deleting.delete()
            return HttpResponse(status=200)
    raise Http404()


def set_bank_info(request):
    """
    Called from payment/update_bank_info, expects POST data
    name: string (len >= 4, max of 22 as defined in the model; represents
    account holder's name)
    account_number: string (at least 8, no more than 17; must be convertible to
    int)
    routing_number: string (exactly 9; must be convertible to int)

    Output: JSON
    """
    if request.method != 'POST':
        return JSON({'error': 'Inappropriate request type.'})
    else:
        name = request.POST.get('name', '')
        acct_number = request.POST.get('account_number', '')
        rout_number = request.POST.get('routing_number', '')

        if not name or not acct_number or not rout_number:
            return JSON({'error': 'Please fill in all fields.'})

        problem = False
        try:
            int(acct_number)
            int(rout_number)
        except ValueError:
            problem = True

        if problem \
                or len(name) < 4 \
                or len(acct_number) < 8 \
                or len(rout_number) != 9:
            return JSON({'error': 'Please enter valid info.'})

        BankInfo.objects.filter(profile=request.user.person.view).delete()
        BankInfo.objects.create(profile=request.user.person.view,
                                routing_number=rout_number,
                                account_number=acct_number,
                                account_holder_name=name)

        return JSON({'success': 'Thank you!'})


@login_required
def card_info(request):
    """
    Called at payment/card_info
    Output: HTML
    """
    cards = CreditCard.objects.filter(user=request.user)
    t = loader.get_template('payment_processing/card_info.html')
    return render_appropriately(request, t, {
        'stripe_publishable': STRIPE_PUBLISHABLE,
        'cards': cards,
        'contentclass': 'dashboard legal'
    })


def add_band_credit(purchase_prices, total, downloadCharge):
    """
    This is used to add the correct amount of hearo bucks to bands' accounts
    for a purchase.

    Called in download_songs, expects input of the form
    purchase_prices: iterable of tuples (representing song/album object, and
    price paid for that object)

    total: int (sum of prices; not necessary, but has already been computed
    when we call this)

    downloadCharge : DownloadCharge object corresponding to purchase

    No return value
    """
    if total <= 0:
        return
    # determine the number of media objects with nonzero price
    numPricedObjects = 0
    for media_object, price in list(purchase_prices.items()):
        if price > 0:
            numPricedObjects += 1
    for song, price in list(purchase_prices.items()):
        song.downloads += 1
        song.save()

    # IMPORTANT: SONG'S TOTAL STRIPE FEE = STRIPE_FEE_PER_SONG + 2.9% OF PRICE
    downloadCharge.stripe_fee_per_song = (Decimal(settings.STRIPE_FEE_FLAT) /
                                          Decimal(numPricedObjects))
    downloadCharge.save()


def cash_out(request):
    """
    Have the current profile cash out the next time an ACH file is created.
    Returns JSON with a success value, and an error message if applicable.
    """
    profile = request.user.profile

    # Return an error if the profile hasn't saved bank info
    if not profile.bank.exists():
        return HttpResponse(content=json.dumps(
            {'success': False,
             'message': 'Add bank info first.'}))

    # Otherwise, we're okay to create a cash out receipt
    create_new_receipt(profile)
    return JSON({'success': True})


def create_new_receipt(profile):
    """
    Create a Receipt object for all the unpaid downloads.  Wrapped in
    transaction management to prevent two simultaneous executions of
    this method from interfering with one another.

    Return the receipt or None if no receipt was created
    """

    downloads = profile.get_downloads_unpaid()

    if len(downloads) == 0:
        return None

    # Create new pending Receipt and assign it to all the unpaid downloads
    new_receipt = Receipt.objects.create(profile=profile, state='pending')
    new_receipt.save()

    for download in downloads:
        download.receipt = new_receipt
        download.save()

    return new_receipt


# Create the ACH file that will be sent to the bank
def create_ach():
    logger = logging.getLogger('payments')

    now = datetime.datetime.now()
    filename = 'ACHP%02d%02d%02d02.ach' % (now.month, now.day, now.year % 100)

    logger.info('Running payments transfer check for %s.', now.strftime('%m/%d/%y'))

    # Hearo cashes out on download charges every day.
    # Get all the downloads that happened yesterday.
    yesterdays_downloads = DownloadCharge.objects.filter(
        date__gt=(now - datetime.timedelta(days=1)),
        total_price__gt=0)

    # Process receipts for users who actually have bank information provided
    receiptqs = Receipt.objects.filter(state='pending',
                                       profile__bank__isnull=False)

    if not (yesterdays_downloads.exists() or receiptqs.exists()):
        logger.info('There\'s no money to move. Exiting.')
        print("NONE")
        return

    with open(filename, 'w') as f:
        file_header = (
            '101 1211403991454497360%02d%02d%02d%02d%02dA094101' %
            # Fixed info, like SVB and our number, etc
            (now.year % 100, now.month, now.day, now.hour,
             now.minute) +  # File creation date/time
            '    SILICON VALLEY BANK           HEARO.FM INC00000000\n'
        )  # Trailing 0's can be anything we want
        #  if we feel the need to do record keeping.
        batch_header = ('5220        HEARO.FM00DISCRETIONARY0DATA1454497360PPD'
                        +  # Discretionary field here (including 0's)
                        'MUSCPAYMNT      %02d%02d%02d   1121140390000001\n' %
                        # MUSCPAYMNT is discretionary, can show up
                        (now.year % 100, now.month, now.day)
                        )  #  on bank statement (trailing spaces are
        #  NOT discretionary)
        # This is the effective entry date, or when we want this to become active. The current date works fine.

        transfer_amounts = {}
        n = 0
        entry_hash = 0

        # Start the file
        f.write(file_header)
        f.write(batch_header)

        # Go through the pending receipts, validate them,
        # and add a line to the ACH file for each transaction we're making.

        # Each of these lines look like this:
        #
        # 6223453453452353245234231    0000017441             11           Artur Sapek  0121140390000001
        #    [routing][  account  ][ total owed ][   user id   ][   account holder   ]           [  n  ]
        # (n = transaction number for this batch)
        for receipt in receiptqs:
            artist = receipt.profile

            # Retrieve the bank info the artist has saved
            try:
                bank_info = BankInfo.objects.get(profile=artist)
            except ObjectDoesNotExist:
                receipt.record_error('User\'s bank info nonexistent')
                logger.error('Failed to credit receipt id=%s; user\'s bank info nonexistent.', receipt.id)
                continue

            routing_number = bank_info.routing_number
            if len(routing_number) != 9:
                # Invalid routing number. I don't know how this could possibly happen
                # because we validate it when saving it, but why not check twice?
                receipt.record_error(
                    'User\'s routing number is %s chars, should be 9' %
                    len(routing_number))
                logger.error('Failed to credit receipt id=%s; routing number (%s) unusable.', receipt.id, routing_number)
                continue

            entry_hash = (entry_hash + int(routing_number[:-1])) % 10000000000

            # Get the account number and account holder names the artist gave us
            account_number = bank_info.account_number.ljust(17)
            account_holder_name = '%22s' % bank_info.account_holder_name

            # We have 15 chars of discretionary data, so why not store the user id
            hearo_id = ('%15d' % artist.pk)[-15:]

            # Get the total profit we owe this artist
            amount = Decimal(receipt.get_total_profit_raw()).quantize(
                Decimal('0.01'))

            # We shouldn't really owe them nothing, or $10,000
            # No money laundering please
            if amount <= 0 or amount >= 9999:
                raise ValueError('Invalid receipt profit amount: %s' % repr(
                    amount))

            # Hold on to this transfer amount for the total down below.
            transfer_amounts[receipt.id] = amount

            # Serialize it to a nice lil' string
            amount_serialized = '%010d' % (100 * amount)
            trace_number = '12114039%07d' % (n + 1)

            # Build the whole entry, write it to the file
            entry_detail = (
                '622%s%s%s%s%s  0%s\n' %
                # those 2 spaces can hold discretionary data (2? srsly wtf banks?)
                (routing_number, account_number, amount_serialized, hearo_id,
                 account_holder_name, trace_number))

            n += 1
            f.write(entry_detail)

            logger.info('Successfully credited $%s to %s (profile id=%s) from receipt id=%s', amount, artist.name, artist.id, receipt.id)

            receipt.state = "batched"
            receipt.save()

        # If there were any downloads yesterday, credit them to Hearo
        if yesterdays_downloads.exists():

            # Now cover the other part: Hearo's 10% from yesterday's downloads.
            # This line should look like this:
            #
            # 6221211403993300874497       0000000000000000000000000          HEARO.FM INC  0121140390000002
            #
            # Which boils down to:
            #
            # 622[routing][    account    ]0000000000000000000000000[     holder name    ]  012114039[  n  ]
            #
            # Where n is the the number of transactions we've already added for cashouts + 1.

            routing_number = '121140399'  # Hearo's SVB routing number.
            entry_hash = (entry_hash + int(routing_number[:-1])) % 10000000000

            account_number = '3300874497'.ljust(17)  # Hearo's SVB account number
            account_holder_name = '%22s' % 'HEARO.FM INC'  # The holder name is just our corporate name
            hearo_id = ('0' * 15)

            # 10% of the last day's charges, minus the portion taken by stripe
            hearo_commission_amount = reduce(
                lambda prev_sum, charge: prev_sum +
                (charge.media_download().hearo_fee()), yesterdays_downloads, 0)
            # If SVB charges us for the transfer from this account, this might have to start with a negative accumulator instead of 0

            transfer_amounts['hearo'] = hearo_commission_amount

            # Serialize the amount into a 10-char string
            hearo_commission_amount_serialized = '%010d' % (
                100 * hearo_commission_amount
            )

            # Only add a transfer to back to Hearo if we actually have any credit from yesterday.
            trace_number = '12114039%07d' % (n + 1)
            entry_detail = (
                '622%s%s%s%s%s  0%s\n' %
                # those 2 spaces can hold discretionary data (2? srsly wtf banks?)
                (routing_number, account_number,
                 hearo_commission_amount_serialized, hearo_id,
                 account_holder_name, trace_number))

            n += 1
            f.write(entry_detail)

            logger.info("Hearo made $%s from yesterday's sales!", hearo_commission_amount)

        entry_hash = '%010d' % entry_hash
        total_credit = sum(transfer_amounts.values())
        total_credit_serialized = '%012d' % (total_credit * 100)
        batch_control = '82200%05d%s000000000000%s1454497360                         121140390000001\n' % (
            n, entry_hash, total_credit_serialized
        )
        file_control = '9000001%06d%08d%s000000000000%s                                       \n' % (
            n + 4, n, entry_hash, total_credit_serialized
        )
        f.write(batch_control)
        f.write(file_control)
        f.close()

    logger.info('Created %s transactions file', filename)
    if hearo_commission_amount > 0:
        logger.info('Hearo commission from yesterday\'s downloads: $%s', hearo_commission_amount)
    if total_credit > 0:
        amt_of_artists = len(list(transfer_amounts.keys())) - 1
        logger.info('Cash-out money sent to %s artist%s: $%s', amt_of_artists, 's' if amt_of_artists > 1 else '', total_credit - hearo_commission_amount)
        logger.info('Transaction batch grand total: $%s', total_credit)

    # Write a temp file with the number of transactions and grand total for our transmittal ACH file generator
    record = open('payment_processing/ach_transmittal_data.tmp.txt', 'w')
    record.write('%s\n%s' % (len(list(transfer_amounts.keys())), total_credit))
    record.close()

    # Throw the filename so that bash can read it
    print(filename)


def create_ach_transmittal_record():
    """
    Generate a transmittal file
    The purpose of this is to confirm the number of transcations and the grand
    total being debited.

    Basically this is just a confirmation that the other ACH file has all
    the correct information.

    Now this is supposed to be sftped over before the larger, more complex ACH
    file.

    """

    logger = logging.getLogger('payments')

    data_file_path = 'payment_processing/ach_transmittal_data.tmp.txt'

    # Read the tmp file for the number of records and the grand total
    ach_transmittal_data_file = open(data_file_path, 'r')
    ach_transmittal_data = ach_transmittal_data_file.read().split('\n')
    ach_transmittal_data_file.close()
    # Remove the tmp file now that we're done with it
    os.remove(data_file_path)

    number = int(ach_transmittal_data[0])
    total = Decimal(ach_transmittal_data[1]).quantize(Decimal('0.01'))

    now = datetime.datetime.now()
    filename = 'ACHP%02d%02d%02d01.ach' % (now.month, now.day, now.year % 100)

    line1 = 'TRANSMTL  121140399 0047723757\r\n'
    line2 = '00472118980000%s%08d%s%012d' % (now.strftime('%y%m%d'), number,
                                             "0" * 12, total * 100)

    # Open a new file
    f = open(filename, 'w')
    f.write(line1)
    f.write(line2)
    f.close()

    # Give bash the name of the file
    print(filename)

    logger.info('Created %s transmittal file for %s transactions totalling $%s', filename, number, total)


class InvalidPurchaseAttemptError(Exception):
    pass


@login_required
def buy_download_queue(request):
    """
    Called from payment/buy_songs. Expects POST data
    Purchase the given songs using the supplied stripe token.
    songs: JSON-encoded list of tuples (representing song_id, price)
    card_token: string (stripe supplied credit card token)(optional, only
    needed with nonzero total price)

    Output: JSON (download_id and total on success, or error message)
    """
    error = None
    view = request.user.person.view
    if request.method == 'POST':
        try:
            total_price = 0

            songs_prices = request.POST.get('songs', None)
            logger.info('songs prices: %s', songs_prices)

            albums_prices = request.POST.get('albums', None)
            logger.info('albums prices: %s', albums_prices))

            tips_prices = request.POST.get('tips', None)
            logger.info('tips prices: %s', tips_prices)

            if not (songs_prices or albums_prices or tips_prices):
                error = 'Attempted to download nothing.'
                raise InvalidPurchaseAttemptError(error)

            download_list = {}

            # Songs we have already purchased should be downloadable for free
            prev_downloads = MediaDownload.objects.filter(charge__profile=view)
            prev_songs = prev_downloads.filter(media__media_song__isnull=False)
            prev_albums = prev_downloads.filter(
                media__media_album__isnull=False)

            prev_songs = [media_down.media.media_song
                          for media_down in prev_songs]
            prev_albums = [media_down.media.media_album
                           for media_down in prev_albums]
            logger.info('previous songs (%s) and albums (%s)',
                prev_songs, prev_albums)

            songs_prices = json.loads(songs_prices)
            albums_prices = json.loads(albums_prices)
            tips_prices = json.loads(tips_prices)
            logger.info(
                'after json loads: album prices: %s, song prices: %s, tip values: %s',
                    albums_prices, songs_prices, tips_prices)

            if len(songs_prices) + len(albums_prices) + len(tips_prices) == 0:
                error = 'Attempted to download nothing.'
                raise InvalidPurchaseAttemptError()

            songs_object_price = [
                ('song', Song.objects.get(pk=song_id), song_price)
                for song_id, song_price in list(songs_prices.items())
            ]
            albums_object_price = [
                ('album', Album.objects.get(pk=album_id), album_price)
                for album_id, album_price in list(albums_prices.items())
            ]
            tips_object_price = [
                ('tip', Profile.objects.get(pk=profile_id), amount)
                for profile_id, amount in list(tips_prices.items())
            ]

            # REMOVE DUPLICATES
            # Not necessary for tips
            songs_object_price = list(set(songs_object_price))
            albums_object_price = list(set(albums_object_price))

            # This whole loop is for input validation, price-checking, etc.
            logger.info('before the loop')
            for media_type, obj, p in (
                songs_object_price + albums_object_price + tips_object_price
            ):
                try:
                    price = Decimal(p).quantize(Decimal('.01'))
                except ValueError:
                    error = 'Invalid price entered'
                    raise InvalidPurchaseAttemptError(error)

                # Set price to 0 if previously purchased
                if (media_type in ('song', 'album') and
                    (obj in prev_songs or obj in prev_albums)):
                    download_list[obj] = Decimal(0)
                    continue

                if media_type in ('song', 'album'):
                    if obj.download_type == 'normal':
                        # ensure the listed price is equal to the price in the
                        # database, to prevent funny business

                        # eg, the artist changed the selling price after the
                        # user added the song to their queue

                        if price == obj.price:
                            total_price += obj.price
                            download_list[obj] = obj.price
                            continue
                        else:
                            error = 'Invalid input.'
                            logger.info('prices not equal')
                            raise InvalidPurchaseAttemptError(error)

                    elif obj.download_type == 'free':
                        download_list[obj] = Decimal(0)
                        continue

                    elif obj.download_type == 'name_price':
                        if price < 0:
                            error = 'Negative prices not allowed.'
                            raise InvalidPurchaseAttemptError(error)
                        elif price > 0:
                            download_list[obj] = Decimal(price)
                            total_price += Decimal(price)
                    else:
                        error = 'Non-downloadable song.'
                        raise InvalidPurchaseAttemptError(error)
                elif media_type == 'tip':
                    total_price += Decimal(price)

            if total_price < 0:
                # We should never reach this point, but just in case.
                error = 'Negative total price not allowed.'
                raise InvalidPurchaseAttemptError(error)
            elif total_price > 0:
                if total_price < .50:
                    error = 'Due to credit card fees, total download '
                    'price must be at least 50 cents.'
                    raise InvalidPurchaseAttemptError(error)
                card = request.POST.get('card_token')
                if not card:
                    error = 'Select a credit card to use.'
                    raise InvalidPurchaseAttemptError(error)

                try:
                    card_used = CreditCard.objects.get(user=request.user,
                                                       stripe_id=card)
                except ObjectDoesNotExist:
                    error = 'Please use a valid card.'
                    raise InvalidPurchaseAttemptError(error)

                # Send the charge to Stripe

                stripe.api_key = STRIPE_SECRET

                try:
                    charge = stripe.Charge.create(
                        amount=int(100 * total_price),  # Charges are in cents
                        currency='usd',
                        customer=card,
                        description='Tune.fm Download')

                    charge_id = charge.id

                except stripe.StripeError as e:
                    error = 'There was a problem processing your '
                    'card: {}'.format(e.message)
                    raise InvalidPurchaseAttemptError(error)
            else:
                # If the download was free, there is no card or charge data
                charge_id = None
                card_used = None

            try:
                songs = [s[1] for s in songs_object_price]
                albums = [a[1] for a in albums_object_price]
                packageid, GN = gangnam_client.request_download(
                    request.user.profile, songs, albums)
            except Exception as e:
                error = 'There was a problem collecting the songs for you: {}'.format(
                    e)
                logger.exception(error, extra={'request': request})
                packageid = None

            # Note, we do not want to error out here, because the customer has
            # already been charged, but we have no record of it yet.

            download_charge = DownloadCharge(
                profile=request.user.profile,
                charge_id=charge_id,
                card_used=card_used,
                total_price=total_price,
                suspicious=(total_price > TOTAL_PURCHASE_VALUE_SUSPICIOUS),
                packageid=packageid)
            download_charge.save()

            if card_used:
                download_charge.last4 = card_used.last4
                download_charge.cardType = card_used.cardType
            if not card_used:
                download_charge.last4 = None
                download_charge.cardType = None
            download_charge.save()

            for mobj, price in list(download_list.items()):
                # Add mediadownload to download_list
                mediadl = MediaDownload(
                    media=mobj,
                    price=price,
                    charge=download_charge,
                    suspicious=(price > INDIVIDUAL_PURCHASE_VALUE_SUSPICIOUS))
                mediadl.save()

                if packageid and not error:
                    # Remove the songs from the queue if we can expect the
                    # download to be successful

                    if type(mobj) == Song:
                        queueOb = QueuedDownload.objects.filter(
                            profile=request.user.profile,
                            song=mobj)
                    elif type(mobj) == Album:
                        queueOb = QueuedDownload.objects.filter(
                            profile=request.user.profile,
                            album=mobj)
                    queueOb.delete()

            # Remove tips from downloadqueue
            queueObjs = QueuedDownload.objects.filter(
                profile=request.user.profile,
                artist_profile__isnull=False)
            queueObjs.delete()

            # give the bands their money!
            add_band_credit(download_list, total_price, download_charge)
        except InvalidPurchaseAttemptError as e:
            error = e.message
            logger.exception(error, extra={'request': request})
        except Exception as e:
            error = 'An unknown error occurred: {}'.format(e)
            logger.exception(error, extra={'request': request})

        if error or not download_charge:
            if not error:
                error = 'An unknown error occurred.'
            return HttpResponse(json.dumps({'error': error}), status=400)
        else:
            logger.info('no error on download charge')
            return HttpResponse(json.dumps({
                'download_id': download_charge.pk,
                'total': float(total_price)
            }))
    else:
        return HttpResponse(
            json.dumps({'error': 'Inappropriate request type.'}), status=400)
