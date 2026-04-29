# An overview of all the available soil 
## parameters for output to the simulation model

<hr style="height:5px; background-color:black; border:none; border-radius:10px">

## NPK Soil Parameters
**Simulation parameters** (To be provided in cropdata dictionary)

| Name         | Description                                                    | Type |              Unit               |
|--------------|----------------------------------------------------------------|:----:|:-------------------------------:|
| NSOILBASE    | Base soil supply of N available through  mineralisation        | SSi  |       $kg \cdot ha^{-1}$        |
| NSOILBASE_FR | Fraction of base soil N that comes available every day         | SSi  |                -                |
| PSOILBASE    | Base soil supply of N available through mineralisation         | SSi  |       $kg \cdot ha^{-1}$        |
| PSOILBASE_FR | Fraction of base soil N that comes available every day         |      |                -                |
| KSOILBASE    | Base soil supply of N available through mineralisation         | SSi  |       $kg \cdot ha^{-1}$        |
| KSOILBASE_FR | Fraction of base soil N that comes available every day         | SSi  |                -                |
|              |                                                                |      |                                 |
| NAVAILI      | Initial N available in the N pool                              | SSi  |       $kg \cdot ha^{-1}$        |
| PAVAILI      | Initial P available in the P pool                              | SSi  |       $kg \cdot ha^{-1}$        |
| KAVAILI      | Initial K available in the K pool                              | SSi  |       $kg \cdot ha^{-1}$        |
|              |                                                                |      |                                 |
| NMAX         | Maximum N available in the N pool                              | SSi  |       $kg \cdot ha^{-1}$        |
| PMAX         | Maximum P available in the N pool                              | SSi  |       $kg \cdot ha^{-1}$        |
| KMAX         | Maximum K available in the N pool                              | SSi  |       $kg \cdot ha^{-1}$        |
|              |                                                                |      |                                 |
| BG_N_SUPPLY  | Background supply of N through atmospheric deposition.         | SSi  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| BG_P_SUPPLY  | Background supply of P through atmospheric deposition.         | SSi  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| BG_K_SUPPLY  | Background supply of K through atmospheric deposition.         | SSi  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
|              |                                                                |      |                                 |
| RNSOILMAX    | Maximum rate of surface N to subsoil                           | SSi  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| RPSOILMAX    | Maximum rate of surface P to subsoil                           | SSi  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| RKSOILMAX    | Maximum rate of surface K to subsoil                           | SSi  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
|              |                                                                |      |                                 |
| RNABSORPTION | Relative rate of N absorption from surface to subsoil          | SSi  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| RPABSORPTION | Relative rate of P absorption from surface to subsoil          | SSi  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
| RKABSORPTION | Relative rate of K absorption from surface to subsoil          | SSi  | $kg \cdot ha^{-1} \cdot d^{-1}$ |
|              |                                                                |      |                                 |
| RNPKRUNOFF   | Relative rate of NPK runoff as a function surface water runoff | SSi  |                -                |

---
## Soil Dynamics Parameters
**Simulation parameters** (To be provided in cropdata dictionary)

| Name   | Description                                                                                    | Type |        Unit         |
|--------|------------------------------------------------------------------------------------------------|:----:|:-------------------:|
| SMFCF  | Field capacity of the soil                                                                     | SSo  |          -          |
| SM0    | Porosity of the soil                                                                           | SSo  |          -          |
| SMW    | Wilting point of the soil                                                                      | SSo  |          -          |
| CRAIRC | Soil critical air content (waterlogging)                                                       | SSo  |          -          |
| SOPE   | maximum percolation rate root zone                                                             | SSo  | $cm \cdot day^{-1}$ |
| KSUB   | maximum percolation rate subsoil                                                               | SSo  | $cm \cdot day^{-1}$ |
| RDMSOL | Soil rootable depth                                                                            | SSo  |        $cm$         |
| IFUNRN | Indicates whether non-infiltrating fraction of rain is a function of storm size (1) or not (0) | SSi  |          -          |
| SSMAX  | Maximum surface storage                                                                        | SSi  |        $cm$         |
| SSI    | Initial surface storage                                                                        | SSi  |        $cm$         |
| WAV    | Initial amount of water in total soil profile                                                  | SSi  |        $cm$         |
| NOTINF | Maximum fraction of rain not-infiltrating into the soil                                        | SSi  |          -          |
| SMLIM  | Initial maximum moisture content in initial rooting depth zone.                                | SSi  |          -          |
           

