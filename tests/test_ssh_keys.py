import pulumi

from infrastructure import PrivateKey

TLS_TYPE = "tls:index/privateKey:PrivateKey"


@pulumi.runtime.test
def test_rsa_key_uses_rsa_bits(mocks):
    key = PrivateKey("rsa-key", algorithm="RSA", rsa_bits=4096)

    def check(_):
        (resource,) = mocks.by_type(TLS_TYPE)
        assert resource.inputs["algorithm"] == "RSA"
        assert resource.inputs["rsaBits"] == 4096
        assert "ecdsaCurve" not in resource.inputs

    return key.private_key.id.apply(check)


@pulumi.runtime.test
def test_rsa_key_default_bits(mocks):
    key = PrivateKey("rsa-key", algorithm="RSA")

    def check(_):
        (resource,) = mocks.by_type(TLS_TYPE)
        assert resource.inputs["rsaBits"] == 2048

    return key.private_key.id.apply(check)


@pulumi.runtime.test
def test_ecdsa_key_uses_curve(mocks):
    key = PrivateKey("ecdsa-key", algorithm="ECDSA", ecdsa_curve="P384")

    def check(_):
        (resource,) = mocks.by_type(TLS_TYPE)
        assert resource.inputs["algorithm"] == "ECDSA"
        assert resource.inputs["ecdsaCurve"] == "P384"
        assert "rsaBits" not in resource.inputs

    return key.private_key.id.apply(check)


@pulumi.runtime.test
def test_ed25519_key_has_no_extra_options(mocks):
    key = PrivateKey("ed-key", algorithm="ED25519")

    def check(_):
        (resource,) = mocks.by_type(TLS_TYPE)
        assert resource.inputs["algorithm"] == "ED25519"
        assert "rsaBits" not in resource.inputs
        assert "ecdsaCurve" not in resource.inputs

    return key.private_key.id.apply(check)


@pulumi.runtime.test
def test_key_is_child_of_component(mocks):
    key = PrivateKey("child-key", algorithm="ED25519")

    def check(urn):
        assert "pkg:index:PrivateKey$" in urn

    return key.private_key.urn.apply(check)


@pulumi.runtime.test
def test_key_aliases_old_parentless_urn(mocks):
    key = PrivateKey("alias-key", algorithm="ED25519")

    def check(aliases):
        assert aliases == [
            "urn:pulumi:test::test::tls:index/privateKey:PrivateKey::alias-key"
        ]

    return pulumi.Output.all(*key.private_key._aliases).apply(check)
