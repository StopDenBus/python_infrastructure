import pulumi
import pulumi_tls as tls

class PrivateKey(pulumi.ComponentResource):
    """Pulumi-Komponente, die ein SSH-/TLS-Schlüsselpaar erzeugt.

    Das Schlüsselpaar ist nach der Initialisierung über das Attribut
    ``private_key`` (``pulumi_tls.PrivateKey``) erreichbar.
    """

    def __init__(self, name: str, algorithm: str, ecdsa_curve: str = None, rsa_bits: int = 2048, opts=None):
        """
        :param name: Name der Ressource.
        :param algorithm: Schlüsselalgorithmus, z. B. ``RSA``, ``ECDSA`` oder ``ED25519``.
        :param ecdsa_curve: Kurve für ``ECDSA`` (z. B. ``P256``); wird sonst ignoriert.
        :param rsa_bits: Schlüssellänge für ``RSA``; wird sonst ignoriert.
        :param opts: Optionale Pulumi-Ressourcenoptionen der Komponente.
        """
        super().__init__('pkg:index:PrivateKey', name, None, opts)
        # Die erzeugte Ressource wird als Kind der Komponente angelegt. Der Alias
        # verhindert, dass bestehende, bisher parent-lose Schlüssel ersetzt werden.
        self.__child_opts = pulumi.ResourceOptions(
            parent=self,
            aliases=[pulumi.Alias(parent=pulumi.ROOT_STACK_RESOURCE)],
        )
        self.__name = name
        self.__algorithm = algorithm
        self.__ecdsa_curve = ecdsa_curve
        self.__rsa_bits = rsa_bits

        self.private_key = self.generate_keys()

        self.register_outputs({
            self.__name: self.private_key
        })

    def generate_keys(self):
        """Erzeugt die ``pulumi_tls.PrivateKey``-Ressource.

        ``ecdsa_curve`` bzw. ``rsa_bits`` werden nur gesetzt, wenn der
        passende Algorithmus (``ECDSA`` bzw. ``RSA``) gewählt wurde.
        """
        return tls.PrivateKey(
                self.__name,
                algorithm=self.__algorithm,
                ecdsa_curve=self.__ecdsa_curve if self.__algorithm == 'ECDSA' else None,
                rsa_bits=self.__rsa_bits if self.__algorithm == 'RSA' else None,
                opts=self.__child_opts,
            )
