/* fanmail.js

*/

//import
/*global
titties,
csrfTOKEN,
update_mail_header,
fanmail,
setupLinks,
jQuery,
userTab,
sendFanMail,
console
*/


(function () {
    function delete_mail() {
        var $msg = $(this);
        $.ajax({
            type: "POST",
            url: '/mail/delete/',
            data: {
                id: parseInt($msg.parent().attr('messageid'), 10),
                csrfmiddlewaretoken: csrfTOKEN
            },
            success: function () {
                $msg.parent().fadeOut(200);
            }
        });
    }

    var fanmail = {
        mark_read: function (msg) {
            $.ajax({
                type: 'POST',
                url: '/mail/mark-read/',
                data: {
                    id: parseInt(msg.parent().attr('messageid'), 10),
                    csrfmiddlewaretoken: csrfTOKEN
                },
                success: function () {
                    msg.parent().removeAttr('unread').find('.unread_dot').remove();
                    fanmail.update_mail_header(parseInt($('#fanmail-envelope').text(), 10) - 1);
                }
            });
        },

        setup_messages: function () {
            var $msg = $('.fanmail_message span.body');
            $msg.linkify();
            $msg.find('a').click(function (e) { e.stopPropagation(); });

            $('.fanmail_message .delete_button').click(delete_mail);
        },

        check_for_new_messages: function () {
            $.get('/mail/check-for-new',
                { id: parseInt($('.inboxContainer').children().first().attr('messageid'), 10) },
                function (response) {
                }
            );
        },

        //called from /ping in utils.js
        update_unread_messages: function (data) {
            fanmail.update_mail_header(data.count);
            if (data.html) {
                var $elt = $(data.html).hide();
                var $firstMessage = $elt.find('.message');
                if ($firstMessage.length) {
                    $firstMessage.click(messageClick);
                }
                $("#inbox").prepend($elt.fadeIn(500))
                    .find('#mail_subhead').fadeOut(300);

                setupLinks();
            }
        },

        update_mail_header: function (count) {
            var $envelope = $('#fanmail-envelope');
            count = Math.min(count, 99);
            if (count === 0) {
                if ($envelope.hasClass('full-envelope')) {
                    $envelope.removeClass('full-envelope');
                    $envelope.find('#count').text(count).hide();
                }
            } else {
                $envelope.find('#count').show().text(count);
                if (!$envelope.hasClass('full-envelope')) {
                    $envelope.addClass('full-envelope');
                }
            }
        },

        sent_mail_tab: function () {
            senttab = $('#sentTab');
            senttab.addClass('tabSelect');
            inboxtab = $('#inboxTab');
            inboxtab.removeClass('tabSelect');
            sentbox = $('#sentbox');
            inbox = $('#inbox');
            sentbox.removeClass('unselected');
            sentbox.addClass('selected');
            inbox.addClass('unselected');
            inbox.removeClass('selected');
        },

        inbox_tab: function () {
            senttab = $('#sentTab');
            senttab.removeClass('tabSelect');
            inboxtab = $('#inboxTab');
            inboxtab.addClass('tabSelect');
            inbox = $('#inbox');
            sentbox = $('#sentbox');
            inbox.removeClass('unselected');
            inbox.addClass('selected');
            sentbox.addClass('unselected');
            sentbox.removeClass('selected');
            console.log(sentbox);
        },

        show_mail_lightbox: function (preload) {
            var darkness = $('<div id="darkness">'), to_field, to_field_clone, offset, offsetParent, headerTab, headerTabOriginal, $dialog;
            darkness.show().click(this.hide_mail_lightbox);

            $('[chill]').remove();

            headerTab = $('#headerUsertab');

            offset = headerTab.find('.imageLink').offset();
            headerTabOriginal = headerTab;
            headerTab = headerTabOriginal.clone();

            headerTab.css({
                position: 'absolute',
                right: '0px',
                top: offset.top,
                'z-index': 2000000005
            }).before(headerTabOriginal);

            $dialog = $('.inboxCompose.forLightbox');

            $dialog.show()
                .before(darkness)
                .css({
                    // left: offset.left - 242
                }).find('input[fillertext="To"]').chill(preload);
            $dialog.find('#send_button').unbind().click(function () {
                sendFanMail($dialog.find('input[fillertext="To"]').attr('selection'),
                    $dialog.find('input[fillertext="Subject"]').val(),
                    $dialog.find('textarea').val()
                );
            });

        },

        hide_mail_lightbox: function () {
            $('#darkness, .inboxCompose.forLightbox, [chill]').hide();
            $('#fanmail-envelope').show();
            $('#headerUsertab').css({ position: 'static' });
            $('.inboxCompose.forLightbox textarea, .inboxCompose.forLightbox input').val('').blur();
        }

    };
    /*
      chill
      an autocomplete plugin for an input:text
      Chooses from people you've fanned.
      Parameters:
        preload (object): optional object with jsonified profile to fill in by default.
    */

    (function ($) {
        $.fn.chill = function (preload) {
            var $c = $('<div class="chill_container" chill></div>'),
                $s = $('<div chill></div>'),
                $d = $('<div class="delete_button" chill></div>'),
                $u,
                $self = this,
                offset = this.offset(),
                keyup_timeout = null,
                query = '',
                saved_val = '',
                selection = null,
                $preloaded_container,
                $preloaded;


            function chill_entry(profile) {
                var entry = $('<div class="chill_entry"></div>').append(new userTab(profile.name, profile.img_path, profile.url, profile.keyword));
                entry.find('a').removeAttr('href');
                return entry;
            }

            function chill_empty_entry(profile) {
                return $('<div class="chill_entry empty">No profiles found</div>');
            }

            function clear() {
                $self.val(query).removeAttr('selection').focus();
                $u.remove();
                $c.show();
                $d.hide();
            }

            function select(opt) {
                var u = opt.find('.usertab'), name_span_span;
                $('body').append(u);
                saved_val = $self.val();
                $d.show();
                $self.val(' ').one('focus', clear);
                $c.hide();
                $u = u.clone();
                $u.attr('chill', '');
                selection = $u.attr('user');
                $self.attr('selection', selection);
                name_span_span = $u.find('a.name span span');
                name_span_span.replaceWith(name_span_span.text());
                $u.css({
                    position: 'fixed',
                    left: offset.left + 5,
                    top: offset.top + (($self.outerHeight() - u.outerHeight()) / 2) + 1 - window.scrollY,
                    'z-index': 20000000006
                }).appendTo($('body')).click(function (e) {
                    e.stopPropagation();
                    clear();
                });
                $u.find('a').click(function (e) {
                    e.preventDefault();
                });
                $d.appendTo($('body')).css({
                    position: 'fixed',
                    left: offset.left + $self.width() - 5,
                    top: offset.top + (($self.outerHeight() - $d.outerHeight()) / 2) - window.scrollY,
                    'z-index': 2000000006
                });
                u.remove();
            }

            $d.click(clear);

            function fill_c(data) {
                $c.empty();
                if (data.length) {
                    $(data).each(function (ind, val) {
                        var entry = chill_entry(val), name, name_field;
                        entry.prependTo($c).mousedown(function () {
                            select($(this));
                        });
                        entry.find('.usertab').click(function (e) {
                            e.stopPropagation();
                            e.preventDefault();
                            select($(this).parent());
                        });
                        entry.find('a').click(function (e) {
                            e.preventDefault();
                        }).unbind();
                        name_field = entry.find('a.name span');
                        name = name_field.text();
                        name_field.replaceWith($('<span>' + name.replace(query, '<span style="font-weight:bold">' + query + '</span>') + '</span>'));
                    });
                } else {
                    chill_empty_entry().prependTo($c);
                }
            }

            function send_query() {
                query = $self.val();
                if (query === '') {
                    $c.empty();
                    return;
                }
                $.get('/chill-plugin-ajax/', { query: query }, function (response) {
                    $c.show();
                    fill_c(response);
                });
            }

            $c.css({
                width: $self.outerWidth() - 2, // 2 becaues of the border.
                left: offset.left,
                top: offset.top + $self.outerHeight() - 1
            });

            $self.keyup(function () {
                clearTimeout(keyup_timeout);
                keyup_timeout = setTimeout(send_query, 300);
            }).blur(function () {
                setTimeout(function () {
                    $c.hide();
                }, 10);
            }).focus(function () {
                if ($self.val() !== '') {
                    $c.show();
                }
            });

            $c.hide().appendTo($('body'));

            if (preload !== undefined) {
                $preloaded_container = $('<div></div>');
                $preloaded = $(new userTab(preload.name, preload.img_path, preload.url, preload.keyword));
                $preloaded_container.append($preloaded);
                select($preloaded_container);
                $self.unbind('focus').focus(function () {
                    $self.blur();
                }); // Don't let people change it
            }

            return this;
        };
    })(jQuery);


    //export
    window.fanmail = fanmail;
}());
