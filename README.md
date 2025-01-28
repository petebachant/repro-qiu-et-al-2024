# Reproducing Qiu et al. (2024) 'Decarbonized energy system planning with high-resolution...'

A [Calkit](https://github.com/calkit/calkit)
project that reproduces the results of:

> Liying Qiu, Rahman Khorramfar, Saurabh Amin, Michael F. Howland,
> Decarbonized energy system planning with high-resolution spatial representation of renewables lowers cost,
> Cell Reports Sustainability,
> Volume 1, Issue 12,
> 2024,
> 100263,
> ISSN 2949-7906,
> https://doi.org/10.1016/j.crsus.2024.100263.

from the Zenodo archive: https://zenodo.org/records/11194453.

## Reproducing

First, if not done already,
[install Calkit](https://docs.calkit.org/installation/)
and
[create a token to integrate with calkit.io](https://docs.calkit.org/cloud-integration/).

Next clone the repo:

```sh
calkit clone https://github.com/petebachant/repro-qiu-et-al-2024
```

Then move into the repo and run the pipeline:

```sh
cd repro-qiu-et-al-2024
calkit run
```
