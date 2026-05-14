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
    mkdir -p $out/bin $out/share

    # Wrap python3 so it runs our app with all deps available
    makeWrapper ${pkgs.python3}/bin/python3 $out/bin/devops-info-service \
      --add-flags "$out/share/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH"

    cp app.py $out/share/app.py
  '';

  # No tests in this simple setup, skip check phase
  doCheck = false;
}
