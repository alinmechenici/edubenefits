---
# Copy this file to _works/<nume-partener>.md and fill it in.
# Put the logo in assets/img/logos/ (JPG or PNG, max 600x600 px, under 200 KB).
# Check before pushing: python3 .github/scripts/validate_partners.py
layout: works-single
title: NUME PARTENER
description: "NUME PARTENER: 10% reducere la ..."   # shown in Google / link previews, max ~155 chars
category: Sanatate             # label shown on the card
category_slug: sanatate        # must be one of the slugs in _data/settings.yml (portfolio.filters)
location: Craiova              # label: Craiova / Oltenia / National / Suceava / Radauti
location_slug: craiova         # craiova | national | suceava  (decides which page lists the partner)
image: assets/img/logos/nume-partener.jpg
short_description: "10% reducere la ..."   # text on the card in the list

# full details (partner page)
live_preview: "#"
info:
  - label: Reducere            # value appears as the badge on the card
    value: 10%

  - label: Telefon             # plain numbers become tap-to-call links
    value: 07xx xxx xxx

  - label: Email
    value: <a href="mailto:contact@exemplu.ro">contact@exemplu.ro</a>

  - label: Website
    value: <a href="https://exemplu.ro" target="_blank">exemplu.ro</a>

  - label: Adresa              # becomes a Google Maps link
    value: Str. Exemplu, nr. 1, Craiova

description1:
  show: yes
  title: "10% reducere la ..."
  text1: "<p>Descrierea ofertei și a partenerului.</p>
  <ul>
  <li>Serviciu 1</li>
  <li>Serviciu 2</li>
  </ul>"
---
