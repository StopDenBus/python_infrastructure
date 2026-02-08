import pulumi
import pulumi_random as random

class RandomPassword(pulumi.ComponentResource):
    def __init__(self, use_case: str, length: int = 16, special: bool = True, opts=None):
        super().__init__('pkg:index:RandomPassword', use_case, None, opts)
        self.__child_opts = pulumi.ResourceOptions(parent=self)
        self.__use_case: str = use_case
        self.__length: int = length
        self.__special: bool = special

        self.random_password: random.RandomPassword = self.random_password()

        self.register_outputs({
            self.__use_case: self.random_password
        })

    def random_password(self ) -> random.RandomPassword:
        return random.RandomPassword(self.__use_case, length=self.__length, special=self.__special, opts=self.__child_opts)
