{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  # "other" tells Nix this isn't a setuptools/flit/poetry project
  format = "other";

  # Python dependencies -- these come from nixpkgs, not PyPI
  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    prometheus-client
  ];

  # makeWrapper lets us wrap the script with the right interpreter
  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin
    cp app.py $out/bin/devops-info-service
    chmod +x $out/bin/devops-info-service

    # Wrap so it finds Python and all dependencies
    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH"
  '';

  # No tests in this simple setup, skip check phase
  doCheck = false;
}
