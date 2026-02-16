from django import forms

class ImportYamlForm(forms.Form):
    yaml_file = forms.FileField(
        label='Выберите YAML файл для импорта',
        help_text='Файл должен быть в формате YAML'
    )