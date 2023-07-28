from django import forms

# from tms.forms import DatePicker


# TODO: This is no longer used, figure out if to remove it or not
class ApplicationForExplorationPermit(forms.Form):
    # Question 1 - Permit Details
    project_name = forms.CharField()
    company_name = forms.CharField()
    company_number = forms.CharField()
    company_address = forms.CharField()
    company_director = forms.CharField()
    company_director_signature = forms.ImageField(label="Director Signature")

    current_date = forms.DateTimeField()

    ahr_name = forms.CharField(label="Authorised Holder Representative")
    ahr_email = forms.EmailField(label="Authorised Holder Representative E-Mail Address")
    ahr_phone = forms.CharField(label="Authorised Holder Representative Phone Number")
    ahr_signature = forms.ImageField(label="Authorised Holder Representative Signature")

    obligations = forms.CharField(widget=forms.Textarea(attrs={'style': 'height: 90px;'}))
    program_fund = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control form-control-sm'

        # This is just a default field entry for developement purposes, delete upon deployment
        # initial = {
        #     'project_name': 'Ravensbourne Project',
        #     'company_name': 'Ravensbourne Minerals Pty Ltd',
        #     'company_number': 'ACN 653 797 730',
        #     'company_address': '7 colo st Arana hills 4504',
        #     'company_director': 'Warwick Anderson',
        #     # 'company_director_signature': 'company director signature',
        #
        #     'ahr_name': 'Warwick Anderson',
        #     'ahr_email': 'warwick@orefox.com',
        #     'ahr_phone': '0437177556',
        #     # 'ahr_signature': 'ahr signature',
        #
        #     'obligations': 'Ravensbourne Minerals Pty Ltd has No other obligations in Qld',
        #     'program_fund': 50000,
        # }
        #
        # for k, v in initial.items():
        #     self.fields[k].initial = v
