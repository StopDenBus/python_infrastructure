import pulumi
import pulumi_proxmoxve as proxmox

from pulumi import ResourceOptions
from pulumi_proxmoxve import Provider
from pulumi_proxmoxve.vm import VirtualMachine

from ..random_password.random_password import RandomPassword

class VirtualMachine(pulumi.ComponentResource):
    """Pulumi-Komponente, die eine Proxmox-VM aus einem bestehenden Template klont.

    Die erzeugte VM ist nach der Initialisierung über das Attribut
    ``virtual_maschine`` (``pulumi_proxmoxve.vm.VirtualMachine``) erreichbar.
    """

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
        """
        :param cpu: CPU-Konfiguration mit den Schlüsseln ``cores`` und ``sockets``.
        :param clone: Klon-Quelle mit den Schlüsseln ``node_name`` und ``vm_id``.
        :param datastore: Datastore für das Cloud-Init-Laufwerk.
        :param disks: Liste von Festplatten, je ein Dict mit ``datastore``, ``size`` und ``format``.
        :param mem: Arbeitsspeicher in MB.
        :param name: Name der VM.
        :param node: Proxmox-Node, auf dem die VM läuft.
        :param network: Netzwerkkonfiguration mit ``domain``, ``dns_servers``,
            ``ipv4_address``, ``ipv4_gateway``, ``ipv6_address`` und ``ipv6_gateway``.
        :param provider: Proxmox-Provider, über den die VM angelegt wird.
        :param user: Benutzer mit ``username``, ``password`` (eine
            :class:`RandomPassword`-Komponente oder eine ``pulumi_random.RandomPassword``-Ressource) und ``public_ssh_keys``.
        :param opts: Optionale Pulumi-Ressourcenoptionen der Komponente.
        """
        super().__init__('pkg:index:VirtualMachine', name, None, opts)
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
        """Legt die Proxmox-VM mit Cloud-Init-Konfiguration an und gibt sie zurück."""
        disks: list = []

        # Aus den übergebenen Festplatten-Dicts werden die Pulumi-Argumente gebaut.
        # Jede Festplatte erhält ein eigenes Interface (scsi0, scsi1, ...).
        for index, disk in enumerate(self.__disks):
            pve_disk = proxmox.vm.VirtualMachineDiskArgs(
                interface=f"scsi{index}",
                datastore_id=disk['datastore'],
                size=disk['size'],
                file_format=disk['format']
            )
            disks.append(pve_disk)

        # Akzeptiert die RandomPassword-Komponente ebenso wie die darin
        # enthaltene pulumi_random-Ressource.
        password = self.__user['password']
        if isinstance(password, RandomPassword):
            password = password.random_password

        # Die VM wird als Kind der Komponente angelegt. Der Alias verhindert, dass
        # eine bestehende, bisher parent-lose VM ersetzt wird.
        virtual_machine: VirtualMachine = proxmox.vm.VirtualMachine(
            opts=ResourceOptions(
                provider=self.__provider,
                parent=self,
                aliases=[pulumi.Alias(parent=pulumi.ROOT_STACK_RESOURCE)],
            ),
            resource_name="vm",
            node_name=self.__node,
            agent=proxmox.vm.VirtualMachineAgentArgs(
                enabled = True,
                trim = True,
                type = "virtio",
                # wait_for_ip=proxmox.vm.VirtualMachineAgentWaitForIpArgs(
                #     ipv4 = True,
                #     ipv6 = True
                # )
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
            # Leeres CD-ROM-Laufwerk, es wird kein ISO eingehängt.
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
            # Cloud-Init: DNS, statische IPs sowie Benutzer samt Passwort und SSH-Keys.
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
                        ipv6=proxmox.vm.VirtualMachineInitializationIpConfigIpv6Args(
                            address = self.__network['ipv6_address'],
                            gateway = self.__network['ipv6_gateway']
                        )
                    )
                ],
                user_account = proxmox.vm.VirtualMachineInitializationUserAccountArgs(
                    username = self.__user['username'],
                    password = password.result,
                    keys = self.__user['public_ssh_keys']
                )
            )
        )

        return virtual_machine