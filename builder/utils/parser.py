import re

def parse_plantuml(uml_text):
    # Patterns for classes, attributes, and relationships
    class_pattern = re.compile(r'class (\w+) {([^}]*)}')
    attribute_pattern = re.compile(r'\s*([\w]+) : ([\w<>]+)')
    relationship_pattern = re.compile(r'(\w+) --> (\w+)')
    inheritance_pattern = re.compile(r'(\w+) <|-- (\w+)')
    enum_pattern = re.compile(r'enum (\w+) {([^}]*)}')
    interface_pattern = re.compile(r'interface (\w+) {([^}]*)}')

    classes = {}
    relationships = []
    inheritances = []
    enums = {}
    interfaces = {}

    # Parse classes and attributes
    for match in class_pattern.finditer(uml_text):
        class_name = match.group(1)
        class_body = match.group(2)
        attributes = attribute_pattern.findall(class_body)
        classes[class_name] = {attr[0]: attr[1] for attr in attributes}

    # Parse relationships
    for match in relationship_pattern.finditer(uml_text):
        source, target = match.groups()
        relationships.append((source, target))

    # Parse inheritances
    for match in inheritance_pattern.finditer(uml_text):
        parent, child = match.groups()
        inheritances.append((parent, child))

    # Parse enums
    for match in enum_pattern.finditer(uml_text):
        enum_name = match.group(1)
        enum_values = match.group(2).strip().split()
        enums[enum_name] = enum_values

    # Parse interfaces
    for match in interface_pattern.finditer(uml_text):
        interface_name = match.group(1)
        interface_body = match.group(2)
        operations = attribute_pattern.findall(interface_body)
        interfaces[interface_name] = operations

    return {
        'classes': classes,
        'relationships': relationships,
        'inheritances': inheritances,
        'enums': enums,
        'interfaces': interfaces
    }

def map_data_type(attr_type):
    """Map UML data types to Django field types."""
    type_map = {
        'String': 'CharField(max_length=255)',
        'Integer': 'IntegerField()',
        'Boolean': 'BooleanField()',
        'DateTime': 'DateTimeField()',
        'Float': 'FloatField()',
        'Text': 'TextField()',
        # Add more mappings as needed
    }
    return type_map.get(attr_type, 'TextField()')  # Default to TextField

def generate_django_models(parsed_data):
    classes = parsed_data['classes']
    inheritances = parsed_data['inheritances']
    enums = parsed_data['enums']

    model_templates = []

    # Generate Django model classes
    for class_name, attributes in classes.items():
        # Handle inheritance
        parent_class = 'models.Model'
        for parent, child in inheritances:
            if child == class_name:
                parent_class = parent

        model_template = f"class {class_name}({parent_class}):\n"

        for attr, attr_type in attributes.items():
            django_type = map_data_type(attr_type)
            model_template += f"    {attr} = models.{django_type}\n"

        model_templates.append(model_template)

    # Generate Django enums
    for enum_name, enum_values in enums.items():
        choices = ", ".join([f"('{val}', '{val}')" for val in enum_values])
        enum_template = f"""
class {enum_name}(models.TextChoices):
    {', '.join(enum_values)} = {choices}
"""
        model_templates.append(enum_template)

    return "\n\n".join(model_templates)

def generate_serializers(parsed_data):
    classes = parsed_data['classes']
    enums = parsed_data['enums']

    serializer_templates = []

    for class_name in classes.keys():
        serializer_template = f"class {class_name}Serializer(serializers.ModelSerializer):\n"
        serializer_template += "    class Meta:\n"
        serializer_template += f"        model = {class_name}\n"
        serializer_template += f"        fields = '__all__'\n"

        serializer_templates.append(serializer_template)

    return "\n\n".join(serializer_templates)

def generate_views(parsed_data):
    classes = parsed_data['classes']

    view_templates = []

    for class_name in classes.keys():
        view_template = f"class {class_name}ViewSet(viewsets.ModelViewSet):\n"
        view_template += f"    queryset = {class_name}.objects.all()\n"
        view_template += f"    serializer_class = {class_name}Serializer\n"

        view_templates.append(view_template)

    return "\n\n".join(view_templates)

def generate_urls(parsed_data):
    classes = parsed_data['classes']

    url_patterns = []

    for class_name in classes.keys():
        url_patterns.append(f"router.register(r'{class_name.lower()}s', {class_name}ViewSet)")

    urls = "\n".join(url_patterns)

    return f"""
from rest_framework import routers
from django.urls import path, include
from .views import *

# Register the ViewSets with a router
router = routers.DefaultRouter()
{urls}

urlpatterns = [
    path('', include(router.urls)),
]
"""