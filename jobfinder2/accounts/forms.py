from django import forms
from django.contrib.auth.forms import UserCreationForm
from jobs.models import Job
from .models import User, UserProfile, Experience, Education

COUNTRIES = [('','--- Pays ---')] + Job.get_country_choices(with_flags=True)

class LoginForm(forms.Form):
    email    = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-input','placeholder':'votre@email.com'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-input','placeholder':'••••••••','id':'pw-login'}))

class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class':'form-input','placeholder':'Prénom'}))
    last_name  = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class':'form-input','placeholder':'Nom'}))
    email      = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-input','placeholder':'email@exemple.com'}))
    role       = forms.ChoiceField(choices=[('jobseeker','Je cherche un emploi'),('employer','Je recrute')],
                    widget=forms.RadioSelect())
    country    = forms.ChoiceField(choices=COUNTRIES, initial='CI', required=False, widget=forms.Select(attrs={'class':'form-input'}))
    password1  = forms.CharField(label='Mot de passe', widget=forms.PasswordInput(attrs={'class':'form-input','placeholder':'••••••••','id':'pw-signup'}))
    password2  = forms.CharField(label='Confirmer', widget=forms.PasswordInput(attrs={'class':'form-input','placeholder':'••••••••'}))

    class Meta:
        model = User
        fields = ('first_name','last_name','email','role','country','password1','password2')

    def clean_country(self):
        value = self.cleaned_data.get('country', '').strip()
        return value or 'CI'

    def save(self, commit=True):
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=self.cleaned_data.get('first_name', ''),
            last_name=self.cleaned_data.get('last_name', ''),
            role=self.cleaned_data.get('role', 'jobseeker'),
            country=self.cleaned_data.get('country') or 'CI',
        )
        if commit:
            user.save()
        UserProfile.objects.get_or_create(user=user)
        return user

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-input'}))
    last_name  = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-input'}))

    class Meta:
        model = UserProfile
        fields = ['avatar','location','phone','linkedin_url','github_url','summary','desired_title']
        widgets = {
            'location':     forms.TextInput(attrs={'class':'form-input','placeholder':'Abidjan, CI'}),
            'phone':        forms.TextInput(attrs={'class':'form-input','placeholder':'+225 XX XX XX XX'}),
            'linkedin_url': forms.URLInput(attrs={'class':'form-input','placeholder':'https://linkedin.com/in/...'}),
            'github_url':   forms.URLInput(attrs={'class':'form-input','placeholder':'https://github.com/...'}),
            'summary':      forms.Textarea(attrs={'class':'form-input','rows':4}),
            'desired_title':forms.TextInput(attrs={'class':'form-input','placeholder':'Data Analyst, Dev Backend...'}),
        }

    def save(self, commit=True):
        instance = self.instance
        has_data = any(
            self.cleaned_data.get(field_name) not in (None, '')
            for field_name in ['location', 'phone', 'linkedin_url', 'github_url', 'summary', 'desired_title']
        )

        if not has_data and self.cleaned_data.get('avatar') in (None, ''):
            if commit:
                instance.save()
            return instance

        if self.cleaned_data.get('avatar') not in (None, ''):
            instance.avatar = self.cleaned_data['avatar']

        for field_name in ['location', 'phone', 'linkedin_url', 'github_url', 'summary', 'desired_title']:
            value = self.cleaned_data.get(field_name)
            if value not in (None, ''):
                setattr(instance, field_name, value)

        if commit:
            instance.save()
        return instance

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['title','company','location','start_date','end_date','is_current','description','technologies']
        widgets = {
            'title':        forms.TextInput(attrs={'class':'form-input','placeholder':'Poste occupé'}),
            'company':      forms.TextInput(attrs={'class':'form-input','placeholder':'Nom de l\'entreprise'}),
            'location':     forms.TextInput(attrs={'class':'form-input','placeholder':'Ville, Pays'}),
            'start_date':   forms.DateInput(attrs={'class':'form-input','type':'date'}),
            'end_date':     forms.DateInput(attrs={'class':'form-input','type':'date'}),
            'description':  forms.Textarea(attrs={'class':'form-input','rows':3}),
            'technologies': forms.TextInput(attrs={'class':'form-input','placeholder':'Python, SQL, React...'}),
        }

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['degree','institution','location','start_year','end_year','gpa']
        widgets = {
            'degree':      forms.TextInput(attrs={'class':'form-input','placeholder':'Licence, Master...'}),
            'institution': forms.TextInput(attrs={'class':'form-input','placeholder':'Nom de l\'établissement'}),
            'location':    forms.TextInput(attrs={'class':'form-input','placeholder':'Ville, Pays'}),
            'start_year':  forms.NumberInput(attrs={'class':'form-input','placeholder':'2020'}),
            'end_year':    forms.NumberInput(attrs={'class':'form-input','placeholder':'2023'}),
            'gpa':         forms.TextInput(attrs={'class':'form-input','placeholder':'Mention / GPA'}),
        }
