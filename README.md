# cosmic-comp + edge_tiling

The Pop!_OS 24.04 build of [cosmic-comp](https://github.com/pop-os/cosmic-comp) with one patch added: an `edge_tiling` setting.
Set it to `false` and a floating window dragged to a screen edge or corner keeps its size.
Without the patch, cosmic-comp tiles or maximizes it.
Edge-sticking (`edge_snap_threshold`) still works.

The patch is in `patches/`.
It is also on the `edge-tiling-toggle` branch, on top of the upstream commit it was written against.

## How it stays current

Every 6 hours `.github/workflows/build.yml` does this:

1. Reads Pop's `cosmic-comp` source package and the upstream commit it was built from.
2. Applies `patches/` to that commit.
3. Builds the `.deb` in an Ubuntu 24.04 container that uses Pop's repo and toolchain.
4. Publishes a signed apt repo to GitHub Pages as version `<pop version>+edgetiling1`.

It skips the build when the published version is already current.
If the patch stops applying, the run fails and GitHub emails you.
Meanwhile apt keeps the last patched build, because the pin below takes priority over Pop's newer, unpatched package.

## One-time setup

Fork:

```sh
gh secret set APT_SIGNING_KEY < private.asc      # see "Signing key"
gh api -X POST repos/{owner}/{repo}/pages -f build_type=workflow
gh workflow run build.yml
```

Signing key (no passphrase, used only to sign this repo):

```sh
export GNUPGHOME=$(mktemp -d)
gpg --batch --passphrase '' --quick-gen-key 'cosmic-comp-edgetiling apt repo' ed25519 sign never
gpg --armor --export-secret-keys > private.asc
gpg --armor --export > public.asc
```

Desktop:

```sh
sudo gpg --dearmor -o /etc/apt/keyrings/cosmic-comp-edgetiling.gpg < public.asc
sudo tee /etc/apt/sources.list.d/cosmic-comp-edgetiling.sources <<'EOF'
Types: deb
URIs: https://danegardner.github.io/cosmic-comp/
Suites: ./
Signed-By: /etc/apt/keyrings/cosmic-comp-edgetiling.gpg
EOF
# Pop pins its own repo at 1001; 1002 makes this one win for cosmic-comp only.
sudo tee /etc/apt/preferences.d/cosmic-comp-edgetiling <<'EOF'
Package: cosmic-comp
Pin: release o=danegardner-cosmic-comp
Pin-Priority: 1002
EOF
sudo apt update && sudo apt install cosmic-comp
echo false > ~/.config/cosmic/com.system76.CosmicComp/v1/edge_tiling
```

Log out and back in to start the new compositor.
After that, `edge_tiling` takes effect as soon as the file is written.

To go back to stock: delete the `.sources` and preferences files, then run `sudo apt update && sudo apt install --allow-downgrades cosmic-comp`.
