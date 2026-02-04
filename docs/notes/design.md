# Purpose

SiteView is intended for visualizing simulation output from EAM, the [E3SM](https://e3sm.org/) Atmosphere Model, in a way that

- focuses primarily on a specific geographical location ("site") such as an [ARM Atmospheric Observatory](https://armgov.svcs.arm.gov/capabilities/observatories) or an arbitrary (lat, lon) combination, but also
- displays the atmospheric conditions for the surrounding area to provide context.

# Types of visualization

The ArrowFlow example at [https://trame.readthedocs.io/en/latest/](https://trame.readthedocs.io/en/latest/) already has most of the key components we'd like to have for SiteView. Below are some initial thoughts.

- 3D (volume) rendering of some variable(s) in the region surrounding the site, with a vertical line indicating the site location.
- Charts showing time evolution of the 3D-rendered variable(s) at the site as well as additional physical quantities at the site. These charts will be static, with time shown on the x-axis, and a line perpendicular to the x-axis indicating the current time of the 3D rendering.
    - For variables with a vertical (lev or ilev) dimension, these charts will be 2D color-shading plots, with the y-axis being the vertical coordinate.
    - For variables with no vertical dimension, the y-axis will be the value of the physical quantity.
- For variables with a vertical dimension, it will also be useful to have animated line charts showing their time evolution in a more quantitative way. In these cases, the x-axis will show the value of a physical quantity and the y-axis will be the vertical coordinate.
 
# Features

- For site selection, allow the user to specify either a (lat, lon) combination or an ARM site (let's include only the 3 [active sites](https://armgov.svcs.arm.gov/capabilities/observatories), NSA, SGP, and ENA, to start with).
- For region selection, allow two options:
  - a lat-lon box, which will be useful for low-latitude and mid-latitude sites;
  - a circle with a user-specified radius in km, which might be more useful for polar regions.
- Allow user to select multiple variables to be displayed as (static or animated) charts in the same session.
- Do we also want 3D rendering of multiple quantities? Possibly. Let's discuss.