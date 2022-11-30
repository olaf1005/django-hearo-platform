/* groups.js

 */

//import
/*global
console,
userTab,
showAreYouSure,
inviteHtml,
sendRequestAjax,
createElem,
csrfTOKEN : false,
makeAdmin,
addUserDropdown,
 */
(function(){

  function deleteGroup(id){
    var grouptag = $("#group_"+id);
    $.ajax({
      type: 'POST',
      url: '/my-account/delete-group-ajax/',
      data: {
	csrfmiddlewaretoken: csrfTOKEN,
	'id':id},
	success: function(data){
	  grouptag.remove();
	  if($('.non_pending_group_description').length === 0){
	    $('#empty_groups_text').show();
	  }
	  //do this to remove the switch in the dropdown
	  //$('.successMessage').show();
	  $('.switch').each(function(index){
	    if($(this).text() === data){
	      $(this).parent().remove();
	    }
	  });
	  //remove the mouseover portion if we only have 1 account left
	  if($(".switch").length === 1){
	    $("#switchAccountsLi").remove();
	  }
	}
    });
  }

  function leave_pending_page(){
    // leave the group, on success, remove the element from the page
    // and add it to active groups
    // if this doesn't work, alert the user to the error
    var r = confirm("Are you sure?");
    if (r == true) {
      var el = this;
      var page_id = $(this).attr('page-id');
      var profileid = $(this).attr('profile-id');
      var page_el = $("#page_" + page_id);
      $.ajax({
	type: 'POST',
	url: '/my-account/delete-member-ajax/',
	data: {csrfmiddlewaretoken: csrfTOKEN,
	  'profileid': profileid,
	  'groupid': page_id
	},
	success: function(data){
	  $(el).parents('li').remove();

	  // if pending groups are now empty, we can remove the tag from the
	  // page
	  if($('#pending-pages ul li').length === 0){
	    $('#pending-pages .empty_media').show();
	    $('#pending-pages ul').hide();
	  }
	},
	error: function(){
	  alert('An error occurred leaving the page.');
	}
      });
    }
  }

  function leave_live_page(){
    var r = confirm("Are you sure?");
    if (r == true) {
      var el = this;
      var page_id = $(this).attr('page-id');
      var profileid = $(this).attr('profile-id');
      var page_el = $("#page_" + page_id);
      $.ajax({
	type: 'POST',
	url: '/my-account/delete-member-ajax/',
	data: {csrfmiddlewaretoken: csrfTOKEN,
	  'profileid': profileid,
	  'groupid': page_id
	},
	success: function(data){
	  $(el).parents('li').remove();

	  // if pending groups are now empty, we can remove the tag from the
	  // page
	  if($('#live-pages ul li').length === 0){
	    $('#live-pages .empty_media').show();
	    $('#live-pages ul').hide();
	  }
	},
	error: function(){
	  alert('An error occurred leaving the page.');
	}
      });
    }
  }

  function view_page(){
    var profile_keyword = $(this).attr('profile-keyword');
    window.location.href='/profile/' + profile_keyword;
  }

  function switch_profile(){
    var profile_keyword = $(this).attr('profile-keyword');
    var profile_id = $(this).attr('profile-id');
    document.location.href='/profile/' + profile_keyword + '?switchid=' + profile_id;
  }

  function join_group(){
    // leave the group, on success, remove the element from the page
    // and add it to active groups
    // if this doesn't work, alert the user to the error
    var el = this;
    var page_id = $(this).attr('page-id');
    var page_el = $("#page_" + page_id);
    $.ajax({
      type: 'POST',
      url: '/my-account/join-page-ajax/',
      data: {csrfmiddlewaretoken: csrfTOKEN,
        'id': page_id
      },
      dataType: "json",
      success: function(data){
        $(el).parents('li').remove();

        // if pending groups are now empty, we can remove the tag from the
        // page
        if($('#pending-pages ul li').length === 0){
          $('#pending-pages .empty_media').show();
          $('#pending-pages ul').hide();
        }

        $('#live-pages ul').html($(data['page_snippet']));

        if($('#live-pages ul li').length !== 0){
          $('#live-pages .empty_media').hide();
          $('#live-pages ul').show();
        }

        // rebind buttons for element added to live section
        $('#live-pages ul li button.leave_page').click(leave_live_page);
        $('button.view_page').click(view_page);
        $('button.switch_to_profile').click(switch_profile);

        my_account_pages_page_hover();

      },
      error: function(){
        alert('An error occurred joining the page.');
      }
    });
  }

  function make_user_admin(){
    var profileid = $(this).attr('profile-id');
    var groupid = $(this).attr('group-id');
    $.ajax({
      type: 'POST',
      url: '/my-account/make-admin-ajax/',
      data: {csrfmiddlewaretoken: csrfTOKEN,'profileid': profileid, 'groupid': groupid},
      success: function(data){
        var elem = $('li#members_'+profileid);
        var clonedelem = elem.clone()
        clonedelem.attr({'id': 'admins_'+profileid});

        clonedelem.find('button.make-admin').removeClass('make-admin').removeClass('arrow-down').addClass('arrow-up').addClass('make-member');
        clonedelem.find('button.delete').attr({'group-type': 'admin'});

        elem.remove();
        $('ul#admins').append(clonedelem);

        $('button.make-admin').click(make_user_admin);
        $('button.make-member').click(make_user_member);
        $('button.delete').click(remove_user_from_page);
      }
    });
  }

  function make_user_member(){
    var profileid = $(this).attr('profile-id');
    var groupid = $(this).attr('group-id');

    // change an admin to a regular member of the group
    $.ajax({
      type: 'POST',
      url: '/my-account/delete-admin-ajax/',
      data: {csrfmiddlewaretoken: csrfTOKEN,
        'profileid': profileid,
        'groupid': groupid
      },
      success: function(id){
        var elem = $('li#admins_'+profileid);
        var clonedelem = elem.clone()
        clonedelem.attr({'id': 'members_'+profileid});

        clonedelem.find('button.make-member').removeClass('make-member').removeClass('arrow-up').addClass('arrow-down').addClass('make-admin');
        clonedelem.find('button.delete').attr({'group-type': 'member'});

        elem.remove();
        $('ul#members').append(clonedelem);

        $('button.make-admin').click(make_user_admin);
        $('button.make-member').click(make_user_member);
        $('button.delete').click(remove_user_from_page);
      },
      error: function(){
        // Note: perhaps show a different error here
        alert('An error occurred demoting the user to a member');
      }
    });
  }

  function remove_user_from_page(){
    var profileid = $(this).attr('profile-id');
    var groupid = $(this).attr('group-id');
    $.ajax({
      type: 'POST',
      url: '/my-account/delete-member-ajax/',
      data: {csrfmiddlewaretoken: csrfTOKEN,
        'profileid': profileid,
        'groupid': groupid
      },
      success: function(id){
        //if removing a regular member, find the element and remove
        //it
        $('li#members_'+profileid).remove();
        $('li#pending_'+profileid).remove();
        $('li#admins_'+profileid).remove();
      },
      error: function(){
        // Note: perhaps show a different error here
        alert('An error occurred removing user as a member');
      }
    });
  }

  function update_membership_percentage() {
      var personid = $(this).attr("person-id");
      var groupid = $(this).attr("group-id");
      var percentageSplit = $(this).val();
      if (percentageSplit > 0) {
        $.ajax({
            type: "POST",
            url: "/my-account/update-membership-split-ajax/",
            data: {
                csrfmiddlewaretoken: csrfTOKEN,
                personid: personid,
                groupid: groupid,
                percentage_split: percentageSplit
            },
            success: function(id) {
                console.info("Updated percentage split ", percentageSplit, id);
            },
            error: function() {
                // Note: perhaps show a different error here
                alert(
                    "An error occurred updating the membership percentage split"
                );
            }
        });
      }
  }

  function addPendingUsertab(profileid, name,picture,url, groupid){
    var row, del, tab;
    row = $('<li id="pending_'+profileid+'"></li>');
    tab = new userTab(name,picture,url);
    del = $('<button class="delete" group-type="member" profile-id="'+profileid+'" group-id="'+groupid+'"></button>');
    percent = $('<input class="percentage_membership_split" profile-id="'+profileid+'" group-id="'+groupid+'" value=""/>');
    $(del).click(remove_user_from_page);
    row.append(tab);
    row.append(del);
    $("#pending ul").append(row);
  }
  /*invite to join your group
    gets called from the profile template (invite button)
    but may get changed to the group tab in my-accounts later using autocomplete
    -calls send_request_ajax in accounts.views.py
    which sends the invitee a fan mail and puts the callers band
    as one of their organizations (but doesn't give them a Membership yet)
    */
  function sendRequestAjax(id, groupid){
    //console.log(id);
    $.ajax({
      type: 'POST',
      url: '/my-account/send-request-ajax/',
      data: {
        csrfmiddlewaretoken: csrfTOKEN,
        'invitee':id,
        'groupid': groupid
      },
      success: function(data){
        var profile = data[0];
        addPendingUsertab(profile.id, profile.name,profile.img_path,profile.url, groupid);
      }
    });
  }
  window.sendRequestAjax = sendRequestAjax;
  //window.setupGroup = setupGroup;
  window.make_user_admin = make_user_admin;
  window.make_user_member = make_user_member;
  window.remove_user_from_page = remove_user_from_page;
  window.leave_pending_page = leave_pending_page;
  window.leave_live_page = leave_live_page;
  window.view_page = view_page;
  window.join_group = join_group;
  window.switch_profile = switch_profile;
  window.update_membership_percentage = update_membership_percentage;


}());
