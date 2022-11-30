from django import forms


class SendReceiveForm(forms.Form):
    send_to = forms.CharField(label="Send to:")
    memo = forms.CharField(widget=forms.Textarea, label="Memo:")
    password = forms.CharField(widget=forms.Textarea, label="Password:")
