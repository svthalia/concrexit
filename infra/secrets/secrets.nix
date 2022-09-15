let
  jelle = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICunYiTe1MOJsGC5OBn69bewMBS5bCCE1WayvM4DZLwE jelle@Jelles-MacBook-Pro.local";
  users = [ jelle ];

  production = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIC3dULYewzf4EKv+KXvneKwqVGNbcFk3Pnb4/iaGTtH1 root@ip-10-0-0-209.eu-west-1.compute.internal";
  staging = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAt1XMYl4R9kUuxrgXCD1Qnp97bED4mMn92BhISgTU+C root@ip-10-0-0-35.eu-west-1.compute.internal";
in
{ 
  "concrexit-production.env.age".publicKeys = users ++ [ production ];
  "concrexit-staging.env.age".publicKeys = users ++ [ staging ];
}
