#!/usr/bin/env bash
check_folder_content() {
  # Checks if all files in foldera are present in folderb no matter their names
  local foldera="$1"
  local folderb="$2"

  # Get sha512sum of all files in foldera (including subfolders)
  local foldera_hashes=$(find "$foldera" -type f -exec sha512sum {} + | awk '{print $1,$2}')

  # Get sha512sum of all files in folderb (including subfolders)
  local folderb_hashes=$(find "$folderb" -type f -exec sha512sum {} + | awk -v folderb="$folderb" -v foldera="$foldera" '{gsub(folderb, foldera, $2); print $1,$2}')

  # Check if all hashes from foldera are present in folderb
  while IFS= read -r hash; do
    if ! grep -q "$hash" <<<"$folderb_hashes"; then
      local file=$(awk '{print $2}' <<<"$hash")
      echo "$file"
    fi
  done <<<"$foldera_hashes"
}

checkup_routine() {
  local signaturefolder="$1"
  local destinationfolder="$2"

  if [ -z "$(ls -A "$destinationfolder")" ]; then
    echo "$destinationfolder is empty, copying from backup"
    if [ -n "$(ls -A "$signaturefolder")" ]; then
      cp -r "$signaturefolder"/* "$destinationfolder"
    else
      echo "$signaturefolder is empty, nothing to copy"
    fi
  else
    echo "$destinationfolder folder is not empty, checking content"
    missing_files=$(check_folder_content "$signaturefolder" "$destinationfolder")
    if [ -n "$missing_files" ]; then
      echo "Copying missing files from $signaturefolder to $destinationfolder"
      while IFS= read -r file; do
        src_file="$signaturefolder/${file#$signaturefolder}"
        dest_file="$destinationfolder/${file#$signaturefolder}"
        dest_dir=$(dirname "$dest_file")
        mkdir -p "$dest_dir"
        cp "$src_file" "$dest_file"
      done <<<"$missing_files"
    else
      echo "All content is already in destination folder"
    fi
  fi
}

#pre check
if [ -z "$BACKUP_FOLDER" ]; then
  echo "BACKUP_FOLDER is not set" >&2
  exit 1
fi

# Config variables
backup_folder="$BACKUP_FOLDER"
cogs_folder="$APPLICATION_FOLDER/cogs"
assets_folder="$APPLICATION_FOLDER/assets"

# Checkup routine on cogs and assets
checkup_routine "$backup_folder/cogs" "$cogs_folder"
checkup_routine "$backup_folder/assets" "$assets_folder"


# push the database in the entrypoint so the prisma file has access to the env variables
prisma db push

# Run the application
exec python3 main.py