let
  pkgs = import <nixpkgs> {};
  stdenv = pkgs.stdenv;
  pypkgs = pkgs.python36Packages;
in stdenv.mkDerivation rec {
  version = "0.0.1";
  name = "gpn-badge-notification-server-${version}";
  src = ./.;
  buildInputs = [pypkgs.flask pypkgs.flask_login pypkgs.werkzeug pypkgs.psycopg2];
}
