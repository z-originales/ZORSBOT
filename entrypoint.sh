#!/bin/bash

# Exporter PGPASSWORD temporairement pour les commandes PostgreSQL
export PGPASSWORD="${POSTGRES_PASSWORD}"

# Attendre que PostgreSQL soit prêt en utilisant pg_isready
dots=""
while ! pg_isready -h "${POSTGRES_HOST}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" > /dev/null 2>&1; do
  dots+="."
  echo -ne "Attente de PostgreSQL$dots\r"
  sleep 2
  if [ ${#dots} -ge 5  ]; then
    dots=""
  fi
done

echo "PostgreSQL est prêt!"

# Variables d'environnement
AUTO_MIGRATE_DB=${AUTO_MIGRATE_DB:-false}
BACKUP_BEFORE_MIGRATE=${BACKUP_BEFORE_MIGRATE:-true}
ALLOW_DESTRUCTIVE_CHANGES=${ALLOW_DESTRUCTIVE_CHANGES:-false}
AUTO_RESTORE_ON_FAIL=${AUTO_RESTORE_ON_FAIL:-true}

# TODO : ajouter une vérification fool proof pour prevenir si allow_destructive_changes est vrai et que auto_restore_on_fail est faux


# Fonction pour effectuer la sauvegarde
do_backup() {
  BACKUP_FILE="/tmp/backups/db_backup_$(date +%Y%m%d_%H%M%S).sql"
  mkdir -p /tmp/backups
  echo "Création d'une sauvegarde de la base de données: $BACKUP_FILE"

  if ! pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$BACKUP_FILE"; then
    echo "❌ Échec de la sauvegarde. La migration est annulée."
    return 1
  fi
  echo "✓ Sauvegarde réussie: $BACKUP_FILE"
  echo "$BACKUP_FILE"
  return 0
}

# Si AUTO_MIGRATE est activé, générer et appliquer les migrations
if [ "$AUTO_MIGRATE_DB" = "true" ]; then
  echo "Vérification des changements de modèles..."

  # Créer une sauvegarde si configuré
  BACKUP_FILE=""
  if [ "$BACKUP_BEFORE_MIGRATE" = "true" ]; then
    if ! BACKUP_FILE=$(do_backup); then
      # Nettoyage du mot de passe avant de quitter
      unset PGPASSWORD
      exit 1
    fi
  fi

  # remove the old migration version from the database to avoid conflicts and force alembic to create a new one
  psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "DELETE FROM alembic_version;" > /dev/null 2>&1

  # Créer d'abord la révision avec --autogenerate
  if ! alembic revision --autogenerate -m "Auto-migration $(date +%Y%m%d_%H%M%S)"; then
    echo "❌ Échec de la création de la révision Alembic (erreur de base de données)."
    # Nettoyage du mot de passe avant de quitter
    unset PGPASSWORD
    exit 1
  fi

  # Récupérer le nom du fichier de la dernière révision créée
  LATEST_REVISION=$(ls -t /app/alembic/versions/*.py 2> /dev/null | head -1)

  # Extract only the revision ID (the first part before the underscore "_")
  REVISION_ID=$(basename "$LATEST_REVISION" .py | cut -d'_' -f1)

  # Vérifier si la migration existe
  if ! [ -z "$LATEST_REVISION" ] && [ -f "$LATEST_REVISION" ]; then
    echo "Nouvelles migrations détectées."

    # Vérifier les changements destructifs
    if [ "$ALLOW_DESTRUCTIVE_CHANGES" != "true" ]; then
      # Générer le SQL pour cette révision spécifique uniquement si nécessaire
      alembic upgrade $REVISION_ID:head --sql 1> /tmp/migration_preview.sql
      if grep -E 'DROP|ALTER COLUMN.*DROP' /tmp/migration_preview.sql; then
        echo "❌ AVERTISSEMENT: Changements destructifs détectés!"
        echo "Pour autoriser ces changements, définissez ALLOW_DESTRUCTIVE_CHANGES=true"
        # Nettoyage du mot de passe avant de quitter
        unset PGPASSWORD
        exit 1
      fi
    fi

    echo "Application des migrations..."
    if alembic upgrade head; then
      echo "✓ Migrations automatiques appliquées avec succès."
      rm -f /app/alembic/versions/*.py
    else
      echo "❌ Échec des migrations automatiques."

      # Restaurer automatiquement si configuré et sauvegarde disponible
      if [ "$AUTO_RESTORE_ON_FAIL" = "true" ] && [ -n "$BACKUP_FILE" ] && [ -f "$BACKUP_FILE" ]; then
        echo "Restauration automatique à partir de la sauvegarde..."
        if psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$BACKUP_FILE"; then
          echo "✓ Base de données restaurée avec succès."
        else
          echo "❌ Échec de la restauration automatique."
        fi
      fi

      # Nettoyage du mot de passe avant de quitter
      unset PGPASSWORD
      exit 1
    fi
  else
    echo "✓ Aucun changement de modèle détecté. Base de données à jour."
  fi
fi

# Nettoyage du mot de passe avant d'exécuter l'application principale
# Cela évite que le mot de passe reste dans l'environnement pendant l'exécution de l'application
unset PGPASSWORD
rm -rf /tmp/*

# Exécuter l'application
echo "Démarrage de l'application..."
exec python3 main.py