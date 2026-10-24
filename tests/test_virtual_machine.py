import pulumi
import pulumi_proxmoxve as proxmox
import pytest

from infrastructure import RandomPassword, VirtualMachine

VM_TYPE = "proxmoxve:VM/virtualMachine:VirtualMachine"


@pytest.fixture
def vm_args(mocks):
    provider = proxmox.Provider(
        "pve",
        endpoint="https://pve.example.com:8006/",
        api_token="user@pve!token=secret",
    )
    password = RandomPassword("vm-password")
    return {
        "cpu": {"cores": 2, "sockets": 1},
        "clone": {"node_name": "pve1", "vm_id": 9000},
        "datastore": "local-lvm",
        "disks": [
            {"datastore": "local-lvm", "size": 20, "format": "raw"},
        ],
        "mem": 2048,
        "name": "test-vm",
        "node": "pve1",
        "network": {
            "domain": "example.com",
            "dns_servers": ["10.0.0.1"],
            "ipv4_address": "10.0.0.10/24",
            "ipv4_gateway": "10.0.0.1",
            "ipv6_address": "fd00::10/64",
            "ipv6_gateway": "fd00::1",
        },
        "provider": provider,
        "user": {
            "username": "admin",
            "password": password.random_password,
            "public_ssh_keys": ["ssh-ed25519 AAAA test"],
        },
    }


def _vm_inputs(mocks):
    (resource,) = mocks.by_type(VM_TYPE)
    return resource.inputs


@pulumi.runtime.test
def test_vm_basic_settings(mocks, vm_args):
    vm = VirtualMachine(**vm_args)

    def check(_):
        inputs = _vm_inputs(mocks)
        assert inputs["name"] == "test-vm"
        assert inputs["nodeName"] == "pve1"
        assert inputs["memory"]["dedicated"] == 2048
        assert inputs["cpu"]["cores"] == 2
        assert inputs["cpu"]["sockets"] == 1
        assert inputs["onBoot"] is True

    return vm.virtual_maschine.id.apply(check)


@pulumi.runtime.test
def test_vm_clone_settings(mocks, vm_args):
    vm = VirtualMachine(**vm_args)

    def check(_):
        clone = _vm_inputs(mocks)["clone"]
        assert clone["nodeName"] == "pve1"
        assert clone["vmId"] == 9000
        assert clone["full"] is True

    return vm.virtual_maschine.id.apply(check)


@pulumi.runtime.test
def test_vm_creates_one_disk_per_entry(mocks, vm_args):
    vm_args["disks"] = [
        {"datastore": "local-lvm", "size": 20, "format": "raw"},
        {"datastore": "ssd", "size": 100, "format": "qcow2"},
    ]
    vm = VirtualMachine(**vm_args)

    def check(_):
        disks = _vm_inputs(mocks)["disks"]
        assert [d["datastoreId"] for d in disks] == ["local-lvm", "ssd"]
        assert [d["size"] for d in disks] == [20, 100]
        assert [d["fileFormat"] for d in disks] == ["raw", "qcow2"]

    return vm.virtual_maschine.id.apply(check)


@pulumi.runtime.test
def test_vm_without_disks(mocks, vm_args):
    vm_args["disks"] = []
    vm = VirtualMachine(**vm_args)

    def check(_):
        assert not _vm_inputs(mocks).get("disks")

    return vm.virtual_maschine.id.apply(check)


@pulumi.runtime.test
def test_vm_cloud_init_network(mocks, vm_args):
    vm = VirtualMachine(**vm_args)

    def check(_):
        init = _vm_inputs(mocks)["initialization"]
        assert init["datastoreId"] == "local-lvm"
        assert init["dns"]["domain"] == "example.com"
        assert init["dns"]["servers"] == ["10.0.0.1"]
        (ip_config,) = init["ipConfigs"]
        assert ip_config["ipv4"] == {"address": "10.0.0.10/24", "gateway": "10.0.0.1"}
        assert ip_config["ipv6"] == {"address": "fd00::10/64", "gateway": "fd00::1"}

    return vm.virtual_maschine.id.apply(check)


@pulumi.runtime.test
def test_vm_cloud_init_user_account(mocks, vm_args):
    vm = VirtualMachine(**vm_args)

    def check(_):
        account = _vm_inputs(mocks)["initialization"]["userAccount"]
        assert account["username"] == "admin"
        assert account["password"] == "mock-password"
        assert account["keys"] == ["ssh-ed25519 AAAA test"]

    return vm.virtual_maschine.id.apply(check)


@pulumi.runtime.test
def test_vm_disks_get_distinct_interfaces(mocks, vm_args):
    vm_args["disks"] = [
        {"datastore": "local-lvm", "size": 20, "format": "raw"},
        {"datastore": "ssd", "size": 100, "format": "qcow2"},
        {"datastore": "ssd", "size": 50, "format": "raw"},
    ]
    vm = VirtualMachine(**vm_args)

    def check(_):
        disks = _vm_inputs(mocks)["disks"]
        assert [d["interface"] for d in disks] == ["scsi0", "scsi1", "scsi2"]

    return vm.virtual_maschine.id.apply(check)


@pulumi.runtime.test
def test_vm_accepts_random_password_component(mocks, vm_args):
    vm_args["user"]["password"] = RandomPassword("component-password")
    vm = VirtualMachine(**vm_args)

    def check(_):
        account = _vm_inputs(mocks)["initialization"]["userAccount"]
        assert account["password"] == "mock-password"

    return vm.virtual_maschine.id.apply(check)


@pulumi.runtime.test
def test_vm_is_child_of_component(mocks, vm_args):
    vm = VirtualMachine(**vm_args)

    def check(urn):
        assert "pkg:index:VirtualMachine$" in urn

    return vm.virtual_maschine.urn.apply(check)


@pulumi.runtime.test
def test_vm_aliases_old_parentless_urn(mocks, vm_args):
    vm = VirtualMachine(**vm_args)

    def check(aliases):
        assert any("pkg:index:VirtualMachine$" not in alias for alias in aliases)
        assert all(alias.endswith("::vm") for alias in aliases)

    return pulumi.Output.all(*vm.virtual_maschine._aliases).apply(check)
