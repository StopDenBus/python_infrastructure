import pulumi

from infrastructure import RandomPassword


@pulumi.runtime.test
def test_default_values(mocks):
    password = RandomPassword("db")

    def check(_):
        (resource,) = mocks.by_type("random:index/randomPassword:RandomPassword")
        assert resource.name == "db"
        assert resource.inputs["length"] == 16
        assert resource.inputs["special"] is True

    return password.random_password.id.apply(check)


@pulumi.runtime.test
def test_custom_values(mocks):
    password = RandomPassword("db", length=32, special=False)

    def check(_):
        (resource,) = mocks.by_type("random:index/randomPassword:RandomPassword")
        assert resource.inputs["length"] == 32
        assert resource.inputs["special"] is False

    return password.random_password.id.apply(check)


@pulumi.runtime.test
def test_password_is_child_of_component(mocks):
    password = RandomPassword("db")

    def check(_):
        assert len(mocks.by_type("pkg:index:RandomPassword")) == 1

    return password.random_password.id.apply(check)


def test_attribute_does_not_shadow_a_method(mocks):
    password = RandomPassword("db")

    assert not callable(password.random_password)
    assert callable(password.create_random_password)
