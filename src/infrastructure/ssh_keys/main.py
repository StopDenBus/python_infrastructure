import pulumi
import pulumi_tls as tls

class PrivateKey(pulumi.ComponentResource):
    def __init__(self, name: str, algorithm: str, ecdsa_curve: str = None, rsa_bits: int = 2048, opts=None):
        super().__init__('pkg:index:PrivateKey', name_me, None, opts)
        child_opts = pulumi.ResourceOptions(parent=self)
        self.__name = name
        self.__algorithm = algorithm
        self.__ecdsa_curve = algorithm
        self.__rsa_bits = rsa_bits

        self.register_outputs({
            self.__name: self.generate_keys()
        })

    def generate_keys():
        return tls.PrivateKey(
                self.__name,
                algorithm=self.__algorithm,
                ecdsa_curve=self.__ecdsa_curve if self.__algorithm == 'ECDSA' else None,
                rsa_bits=self.__rsa_bits if self.__algorithm == 'RSA' else None,
            )
