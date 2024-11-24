# jigsaw_puzzle/forms.py
from django import forms
from .models import JigsawPuzzleRoom

class JigsawPuzzleRoomForm(forms.ModelForm):
    class Meta:
        model = JigsawPuzzleRoom
        fields = ['name', 'puzzle_image', 'difficulty', 'mode']
        widgets = {
            'mode': forms.Select(choices=[('versus', 'Versus'), ('collaborative', 'Collaborative')])
        }