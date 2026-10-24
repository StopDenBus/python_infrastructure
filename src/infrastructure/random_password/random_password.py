import pulumi
import pulumi_random as random

class RandomPassword(pulumi.ComponentResource):
    """Pulumi-Komponente, die ein zufälliges Passwort erzeugt.

    Das Passwort ist nach der Initialisierung über das Attribut
    ``random_password`` (``pulumi_random.RandomPassword``) erreichbar.
    """

    def __init__(self, use_case: str, length: int = 16, special: bool = True, opts=None):
        """
        :param use_case: Verwendungszweck, dient als Ressourcenname.
        :param length: Länge des Passworts.
        :param special: Ob Sonderzeichen verwendet werden dürfen.
        :param opts: Optionale Pulumi-Ressourcenoptionen der Komponente.
        """
        super().__init__('pkg:index:RandomPassword', use_case, None, opts)
        # Die erzeugte Ressource wird als Kind der Komponente angelegt.
        self.__child_opts = pulumi.ResourceOptions(parent=self)
        self.__use_case: str = use_case
        self.__length: int = length
        self.__special: bool = special

        self.random_password: random.RandomPassword = self.create_random_password()

        self.register_outputs({
            self.__use_case: self.random_password
        })

    def create_random_password(self) -> random.RandomPassword:
        """Legt die ``pulumi_random.RandomPassword``-Ressource an und gibt sie zurück."""
        return random.RandomPassword(self.__use_case, length=self.__length, special=self.__special, opts=self.__child_opts)
