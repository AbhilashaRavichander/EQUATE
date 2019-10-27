'''
Data structure to hold numset information
'''


class Numset:
    def __init__(self, value, unit=None, entity=None, approximate=None, frequency=None,
                 change=None, adjective=None, verb=None, location=None, mention=None, position=None):
        self.value = value
        self.unit = unit
        self.entity = entity

        self.approximate = approximate
        self.frequency = frequency
        self.change = change
        self.adjective = adjective
        self.verb = verb
        self.location = location

        self.mention = mention
        self.position = position

    def is_equal(self, numset):
        return int(self.value == numset.value) + int(self.unit == numset.unit) + int(
            self.entity == numset.entity) + int(self.approximate == numset.approximate) + int(
            self.frequency == numset.frequency) + int(self.change == numset.change) + int(
            self.adjective == numset.adjective) + int(self.verb == numset.verb) + int(self.location == numset.location)

    def is_unequal(self, numset):
        return int(self.value != numset.value) + int(self.unit != numset.unit) + int(
            self.entity != numset.entity) + int(self.approximate != numset.approximate) + int(
            self.frequency != numset.frequency) + int(self.change != numset.change) + int(
            self.adjective != numset.adjective) + int(self.verb != numset.verb) + int(self.location != numset.location)

    def set_dict(self, numset_dict):
        if 'Value' in numset_dict:
            self.value = numset_dict['Value']
        if 'Units' in numset_dict:
            self.unit = numset_dict['Units']
        if 'Entities' in numset_dict:
            self.entity = numset_dict['Entities']
        if 'Approximate' in numset_dict:
            self.approximate = numset_dict['Approximate']
        if 'Frequency' in numset_dict:
            self.frequency = numset_dict['Frequency']
        if 'Change' in numset_dict:
            self.change = numset_dict['Change']
        if 'Adjective' in numset_dict:
            self.adjective = numset_dict['Adjective']
        if 'Verb' in numset_dict:
            self.verb = numset_dict['Verb']
        if 'Location' in numset_dict:
            self.location = numset_dict['Location']
        if 'full mention' in numset_dict:
            self.mention = numset_dict['full mention']
        if 'Position' in numset_dict:
            self.position = numset_dict['Position']

    def get_dict(self):
        # Just for compatibility with old data format
        # Remove when integration is tight
        dict_object = {}
        dict_object['Value'] = self.value
        dict_object['Units'] = self.unit
        dict_object['Entities'] = self.entity
        dict_object['Approximate'] = self.approximate
        dict_object['Frequency'] = self.frequency
        dict_object['Change'] = self.change
        dict_object['Adjective'] = self.adjective
        dict_object['Verb'] = self.verb
        dict_object['Location'] = self.location
        dict_object['full mention'] = self.mention
        dict_object['Position'] = self.position
        return dict_object
