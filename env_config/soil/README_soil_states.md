# An overview of all the available soil 
## State and Rate values for output to the simulation model

<hr style="height:5px; background-color:black; border:none; border-radius:10px">

## NPK Soil Dynamics States and Rates
**State variables** (For output to observation space)

| Name        | Description                                              | Pbl |        Unit        |
|-------------|----------------------------------------------------------|:---:|:------------------:|
| NSOIL       | total mineral soil N available at start of growth period |  N  | $kg \cdot ha^{-1}$ |
| PSOIL       | total mineral soil P available at start of growth period |  N  | $kg \cdot ha^{-1}$ |
| KSOIL       | total mineral soil K available at start of growth period |  N  | $kg \cdot ha^{-1}$ |
|             |                                                          |     |                    |
| NAVAIL      | Total mineral N from soil and fertiliser                 |  Y  | $kg \cdot ha^{-1}$ |
| PAVAIL      | Total mineral N from soil and fertiliser                 |  Y  | $kg \cdot ha^{-1}$ |
| KAVAIL      | Total mineral N from soil and fertiliser                 |  Y  | $kg \cdot ha^{-1}$ |
|             |                                                          |     |                    |
| TOTN        | Total mineral N applied by fertilization                 |  Y  | $kg \cdot ha^{-1}$ |
| TOTP        | Total mineral P applied by fertilization                 |  Y  | $kg \cdot ha^{-1}$ |
| TOTK        | Total mineral K applied by fertilization                 |  Y  | $kg \cdot ha^{-1}$ |
|             |                                                          |     |                    |
| SURFACE_N   | Mineral N on surface layer                               |  Y  | $kg \cdot ha^{-1}$ |
| SURFACE_P   | Mineral P on surface layer                               |  Y  | $kg \cdot ha^{-1}$ |
| SURFACE_K   | Mineral K on surface layer                               |  Y  | $kg \cdot ha^{-1}$ |
|             |                                                          |     |                    |
| TOTN_RUNOFF | Total surface N runoff                                   |  Y  | $kg \cdot ha^{-1}$ |
| TOTP_RUNOFF | Total surface N runoff                                   |  Y  | $kg \cdot ha^{-1}$ |
| TOTK_RUNOFF | Total surface N runoff                                   |  Y  | $kg \cdot ha^{-1}$ |

**Rate variables** (For output to observation space)

| Name          | Description                            | Pbl |              Unit               |
|---------------|----------------------------------------|:---:|:-------------------------------:|
| RNSOIL        | Rate of change on total soil mineral N |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| RPSOIL        | Rate of change on total soil mineral P |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| RKSOIL        | Rate of change on total soil mineral K |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
|               |                                        |     |                                 |
| RNAVAIL       | Total change in N availability         |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| RPAVAIL       | Total change in P availability         |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| RKAVAIL       | Total change in K availability         |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
|               |                                        |     |                                 |
| FERT_N_SUPPLY | Rate of supply of fertilizer N         |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |            
| FERT_P_SUPPLY | Rate of Supply of fertilizer P         |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| FERT_K_SUPPLY | Rate of Supply of fertilizer K         |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
|               |                                        |     |                                 |
| RRUNOFF_N     | Rate of N runoff                       |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| RRUNOFF_P     | Rate of P runoff                       |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| RRUNOFF_K     | Rate of K runoff                       |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
|               |                                        |     |                                 |
| RNSUBSOIL     | Rate of N from surface to subsoil      |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| RPSUBSOIL     | Rate of N from surface to subsoil      |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| RKSUBSOIL     | Rate of N from surface to subsoil      |  N  | $kg \cdot ha^{-1} \cdot d^{-1}$ |

---
## Soil Dynamics States and Rates
**State variables:** (For output to observation space)

  [//]: # (TODO: WLOWI is missing Pbl data)
| Name     | Description                                                                                                                                                           | Pbl | Unit |
|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---:|:----:|
| SM       | Volumetric moisture content in root zone                                                                                                                              |  Y  |  -   |
| SS       | Surface storage (layer of water on surface)                                                                                                                           |  N  | $cm$ |
| SSI      | Initial urface storage                                                                                                                                                |  N  | $cm$ |
| WC       | Amount of water in root zone                                                                                                                                          |  N  | $cm$ |
| WI       | Initial amount of water in the root zone                                                                                                                              |  N  | $cm$ |
| WLOW     | Amount of water in the subsoil (between current rooting depth and maximum rootable depth)                                                                             |  N  | $cm$ |
| WLOWI    | Initial amount of water in the subsoil                                                                                                                                |     | $cm$ |
| WWLOW    | Total amount of water in the soil profile $\small WWLOW = WLOW + W$                                                                                                   |  N  | $cm$ |
| WTRAT    | Total water lost as transpiration as calculated by the water balance. This can be different from the CTRAT variable which only counts transpiration for a crop cycle. |  N  | $cm$ |
| EVST     | Total evaporation from the soil surface                                                                                                                               |  N  | $cm$ |
| EVWT     | Total evaporation from a water surface                                                                                                                                |  N  | $cm$ |
| TSR      | Total surface runoff                                                                                                                                                  |  N  | $cm$ |
| RAINT    | Total amount of rainfall ($\small \text{eff + non-eff}$)                                                                                                              |  N  | $cm$ |
| WART     | Amount of water added to root zone by increase of root growth                                                                                                         |  N  | $cm$ |
| TOTINF   | Total amount of infiltration                                                                                                                                          |  N  | $cm$ |
| TOTIRRIG | Total amount of irrigation                                                                                                                                            |  N  | $cm$ |
| TOTIRR   | Total amount of effective irrigation                                                                                                                                  |  N  | $cm$ |
| PERCT    | Total amount of water percolating from rooted zone to subsoil                                                                                                         |  N  | $cm$ |
| LOSST    | Total amount of water lost to deeper soil                                                                                                                             |  N  | $cm$ |
| DSOS     | Days since oxygen stress, accumulates the number of consecutive days of oxygen stress                                                                                 |  Y  |  -   |
| WBALRT   | Checksum for root zone waterbalance                                                                                                                                   |  N  | $cm$ |
| WBALTT   | Checksum for total waterbalance                                                                                                                                       |  N  | $cm$ |

**Rate variables:** (For output to observation space)

| Name        | Description                                                                                                               | Pbl |        Unit         |
|-------------|---------------------------------------------------------------------------------------------------------------------------|:---:|:-------------------:|
| EVS         | Actual evaporation rate from soil                                                                                         |  N  | $cm \cdot day^{-1}$ |
| EVW         | Actual evaporation rate from water surface                                                                                |  N  | $cm \cdot day^{-1}$ |
| WTRA        | Actual transpiration rate from plant canopy, is directly derived from the variable "TRA" in the evapotranspiration module |  N  | $cm \cdot day^{-1}$ |
| RAIN_INF    | Infiltrating rainfall rate for current day                                                                                |  N  | $cm \cdot day^{-1}$ |
| RAIN_NOTINF | Non-infiltrating rainfall rate for current day                                                                            |  N  | $cm \cdot day^{-1}$ |
| RIN         | Infiltration rate for current day                                                                                         |  N  | $cm \cdot day^{-1}$ |
| RIRR        | Effective irrigation rate for current day, computed as irrigation amount * efficiency.                                    |  N  | $cm \cdot day^{-1}$ |
| PERC        | Percolation rate to non-rooted zone                                                                                       |  N  | $cm \cdot day^{-1}$ |
| LOSS        | Rate of water loss to deeper soil                                                                                         |  N  | $cm \cdot day^{-1}$ |
| DW          | Change in amount of water in rooted zone as a result of infiltration, transpiration and evaporation.                      |  N  | $cm \cdot day^{-1}$ |
| DWLOW       | Change in amount of water in subsoil                                                                                      |  N  | $cm \cdot day^{-1}$ |
| DTSR        | Change in surface runoff                                                                                                  |  N  | $cm \cdot day^{-1}$ |
| DSS         | Change in surface storage                                                                                                 |  N  | $cm \cdot day^{-1}$ |
