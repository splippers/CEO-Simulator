#!/usr/bin/env bash
# Import all characters from Jonathan's books into Samba AD.
# Run after `docker compose up -d` when samba-ad is running.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

set -a
[[ -f .env ]] && source .env
set +a

SAMBA_ADMIN_PASS="${SAMBA_ADMIN_PASS}"
AD_CONTAINER="ceo-samba-ad"
UPN_SUFFIX="${DOMAIN:-project6x7.com}"
PASS="${BOOK_USER_PASS:-BookUser2026!}"

# username:Display Name:Given:Surname
USERS=(
  # -- Memoir / Autobiography --
  jonathan_davis:Jonathan Davis:Jonathan:Davis
  "kelz:Kelz:Kelz:(partner)"
  "theodore:Theodore:Theodore:(son)"
  "luke:Luke:Luke:(son)"
  "george:George:George:(son)"
  "aunty_pat:Aunt Pat:Aunt:Pat"
  "stuart_patient:Stuart:Stuart:(patient)"
  "huge_sam:Huge Sam:Huge:Sam"
  "liz_chef:Liz:Liz:(chef)"
  "cloud:Cloud:Cloud:(care-worker)"
  "dr_max:Dr Max:Dr:Max"
  "evangeline:Evangeline:Evangeline:(patient)"
  "iain_patient:Iain:Iain:(patient)"
  "anne_patient:Anne:Anne:(patient)"
  "marge_patient:Marge:Marge:(patient)"
  "erhan:Erhan:Erhan:(case-worker)"
  "neville:Neville:Neville:(staff)"
  "joe_boy:Joe:Joe:(young-author)"
  "nick_brother:Nick:Nick:(brother)"
  "mrs_mann:Mrs Mann:Mrs:Mann"
  "mum:Mum:Mum:(mother)"
  "dad:Dad:Dad:(father)"
  "mr_sheerness:Mr Sheerness:Mr:Sheerness"
  "mr_clint:Mr Clint:Mr:Clint"
  "james_groundsman:James:James:(groundsman)"
  "miss_green:Miss Green:Miss:Green"

  # -- Standalone Stories --
  "malcolm_peters:Malcolm Peters:Malcolm:Peters"
  "carl_scientist:Carl:Carl:(friend)"
  "graeme:Graeme:Graeme:(friend)"
  "clive:Clive:Clive:(cliff)"
  "james_friend:James:James:(friend)"
  "gemma:Gemma:Gemma:(friend)"
  "bob_school:Bob:Bob:(schoolboy)"
  "john_schoolboy:John:John:(schoolboy)"
  "emmeline:Emmeline:Emmeline:(girl)"
  "mr_grimes:Mr Grimes:Mr:Grimes"
  "miss_nix:Miss Nix:Miss:Nix"
  "raymond:Raymond:Raymond:(boy)"
  "thomas_boy:Thomas:Thomas:(boy)"
  "softy_teddy:Softy:Softy:(teddy)"

  # -- Fantasy (Hamster / Ark) --
  "geoff_hamster:Geoff the Hamster:Geoff:Hamster"
  "jack_starposition:Jack Starposition:Jack:Starposition"
  "terry_krackerson:Terry Krackerson:Terry:Krackerson"
  "bernard_gland:Bernard Gland:Bernard:Gland"
  "jethro_whisp:Jethro Whisp:Jethro:Whisp"
  "jetty_arnhold:Jetty Arnhold:Jetty:Arnhold"
  "trina_whisp:Trina Whisp:Trina:Whisp"
  "johann_tardigrade:Johann:Johann:(tardigrade)"
  "octon_fabled:Octon the Fabled:Octon:Fabled"
  "dash_scientist:Dash:Dash:(scientist)"
  "jerome_dash:Jerome Dash:Jerome:Dash"
  "jack_wedlock:Jack Wedlock:Jack:Wedlock"
  "molly_girl:Molly:Molly:(little-girl)"
  "bob_fantasy:Bob:Bob:(fantasy)"
  "jim_pardew:Jim Pardew:Jim:Pardew"
  "stefan_fantasy:Stefan:Stefan:(fantasy)"
  "jyll:Jyll:Jyll:(fantasy)"
  "dave_fantasy:Dave:Dave:(fantasy)"
  "richards:Richards:Richards:(man)"
  "jeff_mammal:Jeff:Jeff:(small-mammal)"

  # -- Historical / Misc --
  "sir_hubert:Sir Hubert S Flange:Sir:Hubert"
  "lord_ernest:Lord Ernest Bell:Lord:Bell"
  "jethro_railway:Jethro:Jethro:(railway-worker)"

  # -- Kitchen Crew: Humans --
  "madge:Madge:Madge:(artist)"
  "henry:Henry:Henry:(accountant)"
  "trevor:Trevor:Trevor:(son)"
  "fiona:Fiona:Fiona:(daughter)"
  "jimmy_toddler:Jimmy:Jimmy:(toddler)"
  "nick_thief:Nick:Nick:(thief)"

  # -- Kitchen Crew: Fork Family --
  "fillip_fork:Fillip Fork:Fillip:Fork"
  "florence_fork:Florence Fork:Florence:Fork"
  "flora_fork:Flora Fork:Flora:Fork"
  "flossie_fork:Flossie Fork:Flossie:Fork"
  "fred_fork:Fred Fork:Fred:Fork"
  "fergus_fork:Fergus Fork:Fergus:Fork"

  # -- Kitchen Crew: Spoon Family --
  "sally_spoon:Sally Spoon:Sally:Spoon"
  "sadie_spoon:Sadie Spoon:Sadie:Spoon"
  "spencer_spoon:Spencer Spoon:Spencer:Spoon"
  "stuart_spoon:Stuart Spoon:Stuart:Spoon"
  "sam_spoon:Sam Spoon:Sam:Spoon"
  "suzy_spoon:Suzy Spoon:Suzy:Spoon"
  "sid_spoon:Sid Spoon:Sid:Spoon"
  "sarah_spoon:Sarah Spoon:Sarah:Spoon"
  "ken_spoon:Ken Spoon:Ken:Spoon"
  "kitty_spoon:Kitty Spoon:Kitty:Spoon"
  "tommy_teaspoon:Tommy Teaspoon:Tommy:Teaspoon"
  "teddy_teaspoon:Teddy Teaspoon:Teddy:Teaspoon"
  "shirley_server:Shirley Spoon:Shirley:Spoon"
  "sharon_server:Sharon Spoon:Sharon:Spoon"

  # -- Kitchen Crew: Jam Spoon --
  "jenny_jamspoon:Jenny Jam-Spoon:Jenny:Jam-Spoon"

  # -- Kitchen Crew: Knife Family --
  "kneil_knife:Kneil Knife:Kneil:Knife"
  "knigel_knife:Knigel Knife:Knigel:Knife"
  "knorma_knife:Knorma Knife:Knorma:Knife"
  "knita_knife:Knita Knife:Knita:Knife"
  "knoreen_knife:Knoreen Knife:Knoreen:Knife"
  "knoeline_knife:Knoeline Knife:Knoeline:Knife"
  "knoel_knife:Knoel Knife:Knoel:Knife"
  "kathy_knife:Kathy Knife:Kathy:Knife"
  "kitty_knife:Kitty Knife:Kitty:Knife"
  "keith_knife:Keith Knife:Keith:Knife"
  "kath_knife:Kath Knife:Kath:Knife"

  # -- Kitchen Crew: Sharp Army --
  "general_carver:General Carver:General:Carver"
  "colonel_breadknife:Colonel Breadknife:Colonel:Breadknife"
  "captain_boning:Captain Boning:Captain:Boning"
  "major_fruitveg:Major Fruit and Veg:Major:Fruit-and-Veg"
  "sergeant_allpurpose:Sergeant All-Purpose:Sergeant:All-Purpose"

  # -- Kitchen Crew: Other Utensils --
  "butts_butterknife:Butts Butterknife:Butts:Butterknife"
  "topsy_corkscrew:Topsy Corkscrew:Topsy:Corkscrew"
  "peter_palette:Peter Pallet Knife:Peter:Pallet"
  "wilma_whisk:Wilma Whisk:Wilma:Whisk"
  "claude_cheeseknife:Claude Cheese Knife:Claude:Cheese-Knife"
  "laddie_ladle:Laddie Ladle:Laddie:Ladle"
  "ted_tenderiser:Ted Tenderiser:Ted:Tenderiser"
  "sophie_sieve:Sophie Sieve:Sophie:Sieve"
  "holly_wood:Holly Wood:Holly:Wood"
  "olive_wood:Olive Wood:Olive:Wood"
  "mable_maple:Mable Maple:Mable:Maple"
  "roland_rollingpin:Roland Rolling Pin:Roland:Rolling-Pin"
  "fred_fishslice:Fred Fish Slice:Fred:Fish-Slice"
  "anna_tongs:Anna Tongs:Anna:Tongs"
  "belle_tongs:Belle Tongs:Belle:Tongs"
  "sid_sharpener:Sid Knife Sharpener:Sid:Sharpener"
  "larry_ladle:Larry Ladle:Larry:Ladle"

  # -- Kitchen Crew: Pets --
  "crumpet_cat:Crumpet:Crumpet:(cat)"
  "wilfrid_dog:Wilfrid:Wilfrid:(dog)"
  "flash_goldfish:Flash:Flash:(goldfish)"
  "flush_goldfish:Flush:Flush:(goldfish)"

  # -- Kitchen Crew: Neighbours --
  "pat_neighbour:Pat:Pat:(neighbour)"
)

total="${#USERS[@]}"
created=0
skipped=0

echo "==> Importing ${total} book characters into Samba AD (${UPN_SUFFIX})"
echo "    password: ${PASS}"
echo ""

for entry in "${USERS[@]}"; do
  IFS=':' read -r uname display given surname <<< "$entry"
  email="${uname}@${UPN_SUFFIX}"

  echo -n "  [$(printf "%3d" $((created + skipped + 1)))/${total}] ${email} (${display}) ... "

  if docker exec "${AD_CONTAINER}" samba-tool user show "${uname}" &>/dev/null; then
    echo "EXISTS"
    skipped=$((skipped + 1))
  else
    result=$(docker exec "${AD_CONTAINER}" samba-tool user create \
      "${uname}" "${PASS}" \
      --mail-address="${email}" \
      --given-name="${given}" \
      --surname="${surname}" \
      --use-username-as-cn 2>&1) && {
      docker exec "${AD_CONTAINER}" samba-tool user setexpiry "${uname}" --noexpiry &>/dev/null
      echo "OK"
      created=$((created + 1))
    } || {
      echo "FAIL: $(echo "$result" | head -1)"
      skipped=$((skipped + 1))
    }
  fi
done

echo ""
echo "==> Done. Created ${created}, skipped ${skipped}/${total} total."
echo "    Login: <username>@${UPN_SUFFIX} / ${PASS}"
