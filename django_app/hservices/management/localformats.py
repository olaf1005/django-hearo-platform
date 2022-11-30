class LocalFormats:
    """
        A helper class to deal with song file formats
    """

    def __init__(self, context):
        """
            creates a versioning object
        """
        self.context = context
        self.formats = self.context.getService("formats")

    def extension(self, stringformat):
        """
            generates the extension string for the stringformat
        """
        stringformat = stringformat.lower().strip()

        if stringformat in list(self.formats["aliases"].keys()):
            stringformat = self.formats["aliases"][stringformat]

        if stringformat in list(self.formats["formats"].keys()):
            return self.formats["formats"][stringformat]["ext"]

        return False

    def suffix(self, stringformat):
        """
            generates the suffix for a given format provide as a String
        """
        stringformat = stringformat.lower().strip()

        if stringformat in list(self.formats["aliases"].keys()):
            stringformat = self.formats["aliases"][stringformat]

        if stringformat in list(self.formats["formats"].keys()):
            return self.formats["formats"][stringformat]["suffix"]

        return False

    def valid(self, stringformat):
        """
            Ensures that a string is a valid format
        """

        stringformat = stringformat.lower().strip()

        if stringformat in list(self.formats["aliases"].keys()):
            return stringformat

        if stringformat in list(self.formats["formats"].keys()):
            return stringformat

        return False
