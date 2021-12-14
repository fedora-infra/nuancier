# -*- mode: ruby -*-
# vi: set ft=ruby :


Vagrant.configure(2) do |config|
  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true
  config.hostmanager.manage_guest = true

  config.vm.define "nuancier" do |nuancier|
    nuancier.vm.box_url = "https://download.fedoraproject.org/pub/fedora/linux/releases/35/Cloud/x86_64/images/Fedora-Cloud-Base-Vagrant-35-1.2.x86_64.vagrant-libvirt.box"
    nuancier.vm.box = "f35-cloud-libvirt"
    nuancier.vm.hostname = "nuancier.tinystage.test"

    nuancier.vm.synced_folder ".", "/vagrant", type: "sshfs"


    nuancier.vm.provider :libvirt do |libvirt|
      libvirt.cpus = 2
      libvirt.memory = 2048
    end

    nuancier.vm.provision "ansible" do |ansible|
      ansible.playbook = "devel/ansible/vagrant-playbook.yml"
      # ansible.config_file = "devel/ansible/ansible.cfg"
      ansible.verbose = true
    end
  end
end
