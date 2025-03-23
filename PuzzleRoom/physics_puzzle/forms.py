from django import forms
from .models import PhysicsPuzzleRoom

class PhysicsPuzzleRoomForm(forms.ModelForm):
    class Meta:
        model = PhysicsPuzzleRoom
        fields = ['name', 'puzzle_image']