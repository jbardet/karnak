#!/usr/bin/env python3
"""
setup_deid_gateway.py
---------------------
Automates three steps against the Karnak REST API:
  1. Upload a de-identification profile YAML file
  2. Create a project linked to that profile (+ generate an HMAC secret)
  3. Add a de-identified DICOM destination to a forward node using that project

Usage
-----
  python setup_deid_gateway.py --profile my-profile.yml \
      --project-name "Clinical Trial 2024" \
      --fwd-aet GATEWAY1 \
      --dest-aet PACS_ANON \
      --dest-host 192.168.1.50 \
      --dest-port 11112

  # Use an existing forward node by ID instead of creating one:
  python setup_deid_gateway.py --profile my-profile.yml \
      --project-name "Clinical Trial 2024" \
      --fwd-id 3 \
      --dest-aet PACS_ANON \
      --dest-host 192.168.1.50 \
      --dest-port 11112
"""

import argparse
import sys
import requests


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def check(r: requests.Response, expected: int, context: str) -> dict:
    if r.status_code != expected:
        die(f"{context} — HTTP {r.status_code}: {r.text}")
    try:
        return r.json()
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Step 1: Upload profile YAML
# ---------------------------------------------------------------------------
def upload_profile(session: requests.Session, base: str, profile_path: str) -> int:
    print(f"[1/3] Uploading profile: {profile_path}")
    with open(profile_path, "rb") as f:
        r = session.post(f"{base}/api/profiles", files={"file": f})
    data = check(r, 201, "Profile upload")
    profile_id = data["id"]
    print(f"      Profile uploaded  id={profile_id}  name={data.get('name', '?')}")
    return profile_id


# ---------------------------------------------------------------------------
# Step 2: Create project + HMAC secret
# ---------------------------------------------------------------------------
def create_project(
    session: requests.Session, base: str, name: str, profile_id: int
) -> int:
    print(f"[2/3] Creating project: {name!r}  (profileId={profile_id})")
    r = session.post(
        f"{base}/api/projects",
        json={"name": name, "profileId": profile_id},
    )
    data = check(r, 201, "Project creation")
    project_id = data["id"]
    print(f"      Project created   id={project_id}")

    # Generate HMAC secret
    r = session.post(
        f"{base}/api/projects/{project_id}/secrets",
        headers={"Content-Type": "application/json"},
        data="{}",
    )
    secret_data = check(r, 201, "Secret generation")
    print(f"      HMAC secret       {secret_data.get('displayKey', '(generated)')}")

    return project_id


# ---------------------------------------------------------------------------
# Step 3: Resolve / create forward node, then add de-identified destination
# ---------------------------------------------------------------------------
def setup_gateway(
    session: requests.Session,
    base: str,
    project_id: int,
    fwd_id: int | None,
    fwd_aet: str | None,
    fwd_description: str,
    dest_aet: str,
    dest_host: str,
    dest_port: int,
    dest_description: str,
) -> None:
    print("[3/3] Configuring gateway destination with de-identification")

    # Resolve forward node
    if fwd_id is not None:
        r = session.get(f"{base}/api/forward-nodes/{fwd_id}")
        node = check(r, 200, f"Get forward node {fwd_id}")
        print(f"      Using existing forward node  id={fwd_id}  aet={node.get('fwdAeTitle', '?')}")
    else:
        if not fwd_aet:
            die("Provide --fwd-id or --fwd-aet to identify the forward node.")
        r = session.post(
            f"{base}/api/forward-nodes",
            json={"fwdAeTitle": fwd_aet, "fwdDescription": fwd_description},
        )
        if r.status_code == 409:
            # Already exists — find it by listing
            all_nodes = check(
                session.get(f"{base}/api/forward-nodes"), 200, "List forward nodes"
            )
            matches = [n for n in all_nodes if n.get("fwdAeTitle") == fwd_aet]
            if not matches:
                die(f"Forward node AET {fwd_aet!r} conflict but not found in list.")
            node = matches[0]
            fwd_id = node["id"]
            print(f"      Forward node already exists  id={fwd_id}  aet={fwd_aet}")
        else:
            node = check(r, 201, "Create forward node")
            fwd_id = node["id"]
            print(f"      Forward node created  id={fwd_id}  aet={fwd_aet}")

    # Add DICOM destination with de-identification
    r = session.post(
        f"{base}/api/forward-nodes/{fwd_id}/destinations",
        json={
            "destinationType": "dicom",
            "description": dest_description,
            "aeTitle": dest_aet,
            "hostname": dest_host,
            "port": dest_port,
            "activate": True,
            "desidentification": True,
            "deIdentificationProject": {"id": project_id},
        },
    )
    dest = check(r, 201, "Create destination")
    print(
        f"      Destination created  id={dest.get('id', '?')}  "
        f"aet={dest_aet}  host={dest_host}:{dest_port}"
    )
    print("      De-identification: ENABLED")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Upload a profile, create a project, and wire it to a Karnak de-id gateway."
    )
    p.add_argument("--base-url", default="http://localhost:8081", help="Karnak base URL")
    p.add_argument("--user", default="admin", help="Basic-auth username")
    p.add_argument("--password", default="karnak", help="Basic-auth password")

    p.add_argument("--profile", required=True, metavar="FILE", help="Path to profile YAML file")
    p.add_argument("--project-name", required=True, metavar="NAME", help="Project name to create")

    # Forward node — provide either an existing ID or an AE Title to create/reuse
    fwd = p.add_mutually_exclusive_group(required=True)
    fwd.add_argument("--fwd-id", type=int, metavar="ID", help="Existing forward node ID")
    fwd.add_argument("--fwd-aet", metavar="AET", help="Forward node AE Title (create if absent)")

    p.add_argument("--fwd-description", default="De-identification gateway", metavar="TEXT")

    p.add_argument("--dest-aet", required=True, metavar="AET", help="Destination AE Title")
    p.add_argument("--dest-host", required=True, metavar="HOST", help="Destination hostname/IP")
    p.add_argument("--dest-port", required=True, type=int, metavar="PORT", help="Destination port")
    p.add_argument(
        "--dest-description", default="De-identified DICOM archive", metavar="TEXT"
    )

    return p.parse_args()


def main() -> None:
    args = parse_args()

    session = requests.Session()
    session.auth = (args.user, args.password)
    base = args.base_url.rstrip("/")

    # Sanity-check connectivity
    try:
        r = session.get(f"{base}/api/forward-nodes", timeout=5)
        if r.status_code == 401:
            die(f"Authentication failed — check --user / --password.")
    except requests.ConnectionError:
        die(f"Cannot reach {base} — is Karnak running?")

    profile_id = upload_profile(session, base, args.profile)
    project_id = create_project(session, base, args.project_name, profile_id)
    setup_gateway(
        session=session,
        base=base,
        project_id=project_id,
        fwd_id=args.fwd_id,
        fwd_aet=args.fwd_aet,
        fwd_description=args.fwd_description,
        dest_aet=args.dest_aet,
        dest_host=args.dest_host,
        dest_port=args.dest_port,
        dest_description=args.dest_description,
    )

    print("\nDone.")
    print(f"  Profile ID : {profile_id}")
    print(f"  Project ID : {project_id}")


if __name__ == "__main__":
    main()
