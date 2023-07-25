from django import forms
from django.forms.widgets import TextInput

class EmailLoginForm(forms.Form):
    email = forms.EmailField()

class NameForm(forms.Form):
    your_name = forms.CharField(label="Your name", max_length=100)

class ProjectForm(forms.Form):
    description = forms.CharField(label="description", max_length=500)
    name = forms.CharField(label="name", max_length=100)
    skill = forms.CharField(label="Skill", max_length=100)
    weekly = forms.CharField(label="Weekly", max_length=300)
    other = forms.CharField(label="Other", max_length=500, required=False)
    deadline = forms.CharField(label="deadline", max_length=500)

