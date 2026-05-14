{ pkgs ? import <nixpkgs> {} }:

pkgs.buildGoModule {
  pname = "devops-info-service-go";
  version = "1.0.0";
  src = ./.;

  # No external deps beyond Go stdlib, so vendorHash can be null
  vendorHash = null;
}
