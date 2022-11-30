/* payment.js

*/

//import
/*global
createElem,
userTab,
console,
csrfTOKEN,
small_fan_button,
*/

(function(){

	function setupPayment(){
		var cashout;
		// get rid of of bigblue 'save' button, and replace it with a cashout button
                hearo.elements.savebutton.hide();
		cashout = createElem('a',{id: 'cashout_link', href: '/my-account/cashout'});
		$(cashout).attr('class','link-btn blue');
		$(cashout).append(createElem('img',{src: '/public/images/creditcard.png'}));
		$(cashout).append("Cash out");
		$('#myAccount_innerPage').prepend(cashout);
		$('#cashout_link img').css('margin-right','8px');
	}

	window.setupPayment = setupPayment;

}());
