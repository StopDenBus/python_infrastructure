import pulumi
import pulumi_proxmoxve as proxmox

from pulumi import ResourceOptions
from pulumi_proxmoxve import Provider
from pulumi_proxmoxve.vm import VirtualMachine

class VirtualMachine(pulumi.ComponentResource):
    def __init__(
            self,
            cpu: dict,
            clone: dict,
            datastore: str,
            disks: list,
            mem: int,
            name: str,
            node: str,
            network: dict,
            provider: Provider,
            user: dict,
            opts=None):
        super().__init__('pkg:index:VirtualMachine', name, None, opts)
        child_opts = pulumi.ResourceOptions(parent=self)
        self.__cpu: dict = cpu
        self.__clone: dict = clone
        self.__datastore: str = datastore
        self.__disks: list = disks
        self.__mem: int = mem
        self.__name = name
        self.__node = node
        self.__network = network
        self.__provider = provider
        self.__user = user

        self.virtual_maschine = self.create_virtual_machine()

        self.register_outputs({
            self.__name: self.virtual_maschine
        })

    def create_virtual_machine(self) -> VirtualMachine:
        disks: list = []

        for disk in self.__disks:
            pve_disk = proxmox.vm.VirtualMachineDiskArgs(
                interface="scsi0",
                datastore_id=disk['datastore'],
                size=disk['size'],
                file_format=disk['format']
            )
            disks.append(pve_disk)

        virtual_machine: VirtualMachine = proxmox.vm.VirtualMachine(
            opts=ResourceOptions(provider=self.__provider),
            resource_name="vm",
            node_name=self.__node,
            agent=proxmox.vm.VirtualMachineAgentArgs(
                enabled=False,
                trim=True,
                type="virtio"
            ),
            bios="seabios",
            cpu=proxmox.vm.VirtualMachineCpuArgs(
                cores=self.__cpu['cores'],
                sockets=self.__cpu['sockets']
            ),
            clone=proxmox.vm.VirtualMachineCloneArgs(
                node_name=self.__clone['node_name'],
                vm_id=self.__clone['vm_id'],
                full=True
            ),
            cdrom=proxmox.vm.VirtualMachineCdromArgs(
                file_id='none'
            ),
            disks=disks,
            memory=proxmox.vm.VirtualMachineMemoryArgs(
                dedicated=self.__mem
            ),
            name=self.__name,
            network_devices=[
                proxmox.vm.VirtualMachineNetworkDeviceArgs(
                    bridge="vmbr0",
                    model="virtio"
                )
            ],
            on_boot=True,
            operating_system=proxmox.vm.VirtualMachineOperatingSystemArgs(type="l26"),
            initialization=proxmox.vm.VirtualMachineInitializationArgs(
                type="nocloud",
                datastore_id = self.__datastore,
                dns=proxmox.vm.VirtualMachineInitializationDnsArgs(
                    domain = self.__network['domain'],
                    servers = self.__network['dns_servers']
                ),
                ip_configs=[
                    proxmox.vm.VirtualMachineInitializationIpConfigArgs(
                        ipv4=proxmox.vm.VirtualMachineInitializationIpConfigIpv4Args(
                            address = self.__network['ipv4_address'],
                            gateway = self.__network['ipv4_gateway']
                        ),
                        # ipv6=proxmox.vm.VirtualMachineInitializationIpConfigIpv6Args(
                        #     address="fd91:0812:a17f:6194::10/64",
                        #     gateway="fd91:0812:a17f:6194::1"
                        # )
                    )
                ],
                user_account = proxmox.vm.VirtualMachineInitializationUserAccountArgs(
                    username = self.__user['username'],
                    password = self.__user['password'].result.apply(lambda result: result),
                    keys = self.__user['public_ssh_keys']
                )
            )
        )

        return virtual_machine