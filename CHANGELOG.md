# CHANGELOG

<!-- version list -->

## v1.3.1 (2026-10-14)

### Bug Fixes

- **charts**: Make toolbar easier to spot
  ([`08b270f`](https://github.com/Kitware/SiteView/commit/08b270f945f6acb9a985413faee67b214317f92a))

- **cli**: Add --version and clean up typos and debug comments
  ([`20e0c63`](https://github.com/Kitware/SiteView/commit/20e0c63a870f2a9ad3c9a67cee21f68f5db9cca5))

- **data-model**: Fix type
  ([`c19d547`](https://github.com/Kitware/SiteView/commit/c19d547a9c8d471b5b01ebae76da0748c8868e75))

- **data-model**: Handle empty time axis and selection edge cases
  ([`c945aef`](https://github.com/Kitware/SiteView/commit/c945aef13809963cc392edf34504fb71140d7940))

- **dock**: Restore analysis panels on reload and new browser tabs
  ([`d56b9a7`](https://github.com/Kitware/SiteView/commit/d56b9a7db9a7cccaaaa0e70fee3686c4b504cea6))

- **edges**: Add toggle button for h/vslice
  ([`67a8ff0`](https://github.com/Kitware/SiteView/commit/67a8ff0bb0c2333628efa47e8296f42290467876))

- **export**: Add export capability
  ([`3513875`](https://github.com/Kitware/SiteView/commit/35138752a57417cbf28bc447664293793f28512f))

- **find-data**: Add helper to insert available var name
  ([`9a9a415`](https://github.com/Kitware/SiteView/commit/9a9a415a7b2d154b1d1cb38cf5ab48feaae232dc))

- **hover**: Add scalar value
  ([`b084368`](https://github.com/Kitware/SiteView/commit/b084368615becb407dbead9e0fa13dbe9367894a))

- **keyboard**: Add shortcuts
  ([`eff89e3`](https://github.com/Kitware/SiteView/commit/eff89e3c299a6b3ec45f9e93f989d0d56d02e572))

- **labels**: Add labels to sliders
  ([`3f99e63`](https://github.com/Kitware/SiteView/commit/3f99e63724fdb58030b8eb0d79115187d258507c))

- **layout**: Improve ui layout
  ([`08062f1`](https://github.com/Kitware/SiteView/commit/08062f1eec95b5dd2bdda2314560e854dff94c35))

- **line-chart**: Properly label time
  ([`640f025`](https://github.com/Kitware/SiteView/commit/640f0254bb2b5ba8b74e506aab697dd4e4ea5e75))

- **map**: Make it interactive to pick location
  ([`47df25a`](https://github.com/Kitware/SiteView/commit/47df25a907e78bd38f3dd46e42913204e0c0b3d8))

- **map**: Place the data region of meshes within 0-180E correctly
  ([`ab294d8`](https://github.com/Kitware/SiteView/commit/ab294d84047677da62997241916187d681fbcb69))

- **orientation**: Zoom to make it bigger
  ([`55bf793`](https://github.com/Kitware/SiteView/commit/55bf7932d9385c89055663247397795788689ed5))

- **reader**: Derive levels from a single hyam/hybm pair
  ([`a9a1a35`](https://github.com/Kitware/SiteView/commit/a9a1a35ec0010af756351212d35bc321bc70372a))

- **site**: Homogeneous button height
  ([`f81c552`](https://github.com/Kitware/SiteView/commit/f81c552072f54f400524fe08ddab4509cbe8c2b9))

- **stepper**: Use stepper for initial site and field selection
  ([`9f475d9`](https://github.com/Kitware/SiteView/commit/9f475d985f2a7b0e503171c5193ba664318719e4))

- **theme**: Allow uniform theme in ui
  ([`42b783b`](https://github.com/Kitware/SiteView/commit/42b783b5b6321b1c2e065bafbe60413234e281cc))

- **time**: Display proper date
  ([`48fda00`](https://github.com/Kitware/SiteView/commit/48fda00f79210221e7b8da79ef6ea99cd2fdd02a))

- **ui**: Improve look and concistency
  ([`3c130bf`](https://github.com/Kitware/SiteView/commit/3c130bf9a56d5543646fe11bc1fdd6ac77e6be02))

- **ui**: Loading and empty placeholder
  ([`223a3ad`](https://github.com/Kitware/SiteView/commit/223a3ada7167aa27d9854475ebfee1158199ad13))

- **ui**: Small fixes
  ([`2ad1805`](https://github.com/Kitware/SiteView/commit/2ad18053ffa8dd37f830da8628ceefd2bf4da722))

- **vuetify**: Migrate to v4
  ([`6aebc65`](https://github.com/Kitware/SiteView/commit/6aebc65d55cdbfdc576c559ce57998c3c05fe24e))

### Continuous Integration

- Run tests in the nox environment and drop template leftovers
  ([`0a8e37e`](https://github.com/Kitware/SiteView/commit/0a8e37e28bf4909e4dcfec064729288e8a29377b))

- Update rca
  ([`ec30ad9`](https://github.com/Kitware/SiteView/commit/ec30ad9401c6e724e5c4d47c8502702065d2a1bb))

### Documentation

- Explain how time steps are handled with several data files
  ([`752da45`](https://github.com/Kitware/SiteView/commit/752da4595a3fa2fc6973e8296a369009c77e4941))

- Update readme pictures
  ([`aeab31a`](https://github.com/Kitware/SiteView/commit/aeab31ac8882cf8b8681bc5df06d3511dcec2b25))

- Update readme pictures
  ([`519c6b5`](https://github.com/Kitware/SiteView/commit/519c6b5afbf6c68e56585256ca88cfff68e2f112))

### Refactoring

- **viz3d**: Split the 3D view into a package
  ([`cf4409c`](https://github.com/Kitware/SiteView/commit/cf4409c3f4270eb6d60d216c1e8e7f8aa8ca7b38))

### Testing

- Cover readers, helpers and region selection with synthetic data
  ([`982f1a9`](https://github.com/Kitware/SiteView/commit/982f1a960c010a3dea52906cbbe7f01af1b6032a))


## v1.3.0 (2026-10-13)

### Bug Fixes

- **chart**: Allow to plot surface variable
  ([`cff8b9a`](https://github.com/Kitware/SiteView/commit/cff8b9a79313ef1f99105b172f36d79daa0df702))

- **color**: Sync 3d and plotly
  ([`bc628b7`](https://github.com/Kitware/SiteView/commit/bc628b7d80e87a43af740f535b99d7e9893916c8))

- **continents**: Use more precise borders
  ([`9be72ea`](https://github.com/Kitware/SiteView/commit/9be72ea1af341eca620e0c668aa21c1ab25fdbde))

- **histogram**: Improve usability
  ([`5dcb104`](https://github.com/Kitware/SiteView/commit/5dcb10423a9ac15438798aa1a6d4115bbb89d279))

- **orientation**: Properly layout data vertically
  ([`dceaaf5`](https://github.com/Kitware/SiteView/commit/dceaaf51e28af691381bc0696cdfa0964e3306f5))

- **reader**: Add surface reader
  ([`4931f6c`](https://github.com/Kitware/SiteView/commit/4931f6c80a1ebfcd950557d0b9026b720a66e3cd))

- **site-selection**: Improve layout of site selection
  ([`8fcb310`](https://github.com/Kitware/SiteView/commit/8fcb3108d351afd99164f01a3f3f08bea081fa63))

### Features

- **col**: Enable picking for column selection
  ([`6083ced`](https://github.com/Kitware/SiteView/commit/6083ced49edea955ee5b16429787f58261ec92d3))

- **surface**: Integrate into 3d view
  ([`d9f96b1`](https://github.com/Kitware/SiteView/commit/d9f96b15a6a5f101a5971b4a2501dda1eeebe418))


## v1.2.0 (2026-10-02)

### Bug Fixes

- **analysis**: Allow data reload
  ([`36e3a14`](https://github.com/Kitware/SiteView/commit/36e3a144e8480787cec49c05a4f971a113d3e7dd))

- **col**: Provide feedback in 3D view
  ([`31abad9`](https://github.com/Kitware/SiteView/commit/31abad9a4581f0ee457cee88b7e3b6f39ab5e5d2))

- **col**: Sorted column menus
  ([`04c595b`](https://github.com/Kitware/SiteView/commit/04c595bd8448255d3ab235a50345f2d5360704e7))

- **col**: Use lat/lon for label
  ([`d49bbef`](https://github.com/Kitware/SiteView/commit/d49bbef0f6cca13f58c5b0b0a9abdfee017030f9))

- **data_model**: Add page/dialog tracking
  ([`a6a3b9d`](https://github.com/Kitware/SiteView/commit/a6a3b9d89da906000bdd90cb6a91a0dd2fcbe25f))

- **earth**: Make it brighter
  ([`2251479`](https://github.com/Kitware/SiteView/commit/225147970c105e6a9198a70f720db66a12526d8a))

- **footer**: Add tooltip
  ([`388b47f`](https://github.com/Kitware/SiteView/commit/388b47f494e379991230621ee348dd3662a1a87a))

- **line-plot**: Use proper altitude data
  ([`5dd3059`](https://github.com/Kitware/SiteView/commit/5dd3059b99eefb0c6ef10009c83a7cb8741c68ac))

- **pages**: Remove pages
  ([`2984630`](https://github.com/Kitware/SiteView/commit/298463019eaf17fca52f598f0a4e44a0606bcd04))

- **pages**: Use dialog and allow back and forth
  ([`cbc6d60`](https://github.com/Kitware/SiteView/commit/cbc6d60289b9587be8e325acf056f2e2fe004376))

- **site**: Put map on the same line as form
  ([`9931edd`](https://github.com/Kitware/SiteView/commit/9931eddde5ead34de395fb2d6d01d98c6d06f9a6))

- **welcome**: Add welcome page
  ([`e5a129a`](https://github.com/Kitware/SiteView/commit/e5a129a90ea4a67f7615072000682928b0a74ae7))

### Features

- **find data**: Add find data with formula
  ([`2b50ace`](https://github.com/Kitware/SiteView/commit/2b50acea1ba23a540651ad990321f846475e4184))

- **grid**: Add grid level
  ([`99dda3e`](https://github.com/Kitware/SiteView/commit/99dda3e988edae2cf03a85309a6752a4194d8f84))

- **heatmap**: Add multi-heatmap support
  ([`de17a4c`](https://github.com/Kitware/SiteView/commit/de17a4c80a9618e57ef9018c76617ac834aeea4b))

- **histogram**: Add data distribution feedback
  ([`c937299`](https://github.com/Kitware/SiteView/commit/c9372991f34b38678f44d26c439500b294bb565e))

- **interaction**: Improve interaction
  ([`f526865`](https://github.com/Kitware/SiteView/commit/f526865b0366e895ee334d308c8e6af384a349ef))

- **orientation**: Add orientation axis
  ([`918b90b`](https://github.com/Kitware/SiteView/commit/918b90b19785542bcd097fb6a56120b5a10639e4))

- **region**: Highlight region on orientation marker
  ([`77c53ce`](https://github.com/Kitware/SiteView/commit/77c53ce69d280886193c68825141b3bdba3a2849))


## v1.1.2 (2026-09-28)

### Bug Fixes

- **data-region**: Only show regions when needed
  ([`157f034`](https://github.com/Kitware/SiteView/commit/157f034bc2598ccf50d130f9331234b1fa556bfa))

- **field**: Link volume field selection to heatmap field
  ([`0060363`](https://github.com/Kitware/SiteView/commit/00603630ef944334f5c87f157c05afe69556763a))

- **heatmap**: Better axis and labels
  ([`42ee524`](https://github.com/Kitware/SiteView/commit/42ee5247eb51b5265cedf3c0f7fa599979413414))

- **lev/z**: Flip z orientation
  ([`c4c0797`](https://github.com/Kitware/SiteView/commit/c4c0797d0f259b8f240574c33aaa99b7683029d3))

- **radius**: Km to degree conversion
  ([`1624415`](https://github.com/Kitware/SiteView/commit/162441531f40ebb27c5569c2ead9779dd1ab1470))


## v1.1.1 (2026-09-15)

### Bug Fixes

- **color_by**: Start with first field
  ([`71abb79`](https://github.com/Kitware/SiteView/commit/71abb79eeb92be8f68af1a2e19e2049583f39d6a))

- **view-up**: Reset camera keep earth up
  ([`cff29b8`](https://github.com/Kitware/SiteView/commit/cff29b84832b28ade2184666980c659556ffdba8))


## v1.1.0 (2026-09-15)

### Bug Fixes

- **cli**: Tag args as required
  ([`570be1f`](https://github.com/Kitware/SiteView/commit/570be1f8c57dadbdc540502529e5ac6129d8a430))

- **rca**: Use rca for remote rendering
  ([`422c032`](https://github.com/Kitware/SiteView/commit/422c03278efe11188b048d3aba614619efb1427f))

- **slice**: Isolate vslice/hslice behavior
  ([`f068ca1`](https://github.com/Kitware/SiteView/commit/f068ca1963b494f1a262f2e179fa86bbe2579e0f))

### Features

- **cloud**: Add cloud visualization
  ([`7f02278`](https://github.com/Kitware/SiteView/commit/7f02278c9999a14c8b6f32ae31499825c216f31a))

- **earth**: Add projection and earth context
  ([`272a800`](https://github.com/Kitware/SiteView/commit/272a800f9de6be0d4c564552baacf082bb038e9d))

- **v-slice**: Add vertical slice
  ([`b7eba33`](https://github.com/Kitware/SiteView/commit/b7eba3397f220e74146c20b88e26018a3fc86e10))

- **zScale**: Add z scaling control
  ([`5145a2e`](https://github.com/Kitware/SiteView/commit/5145a2ea3c4c5e0ac91735a39cbbc60310183a8c))


## v1.0.2 (2026-07-23)

### Bug Fixes

- **chart**: Add cell time chart
  ([`84e1670`](https://github.com/Kitware/SiteView/commit/84e16703a1d9c4b0bdc69368a34cc18f931a7c1e))


## v1.0.1 (2026-07-23)

### Bug Fixes

- **pypi**: Properly bundle assets
  ([`1fd6280`](https://github.com/Kitware/SiteView/commit/1fd62800b077f67129aeb26731376a0402630a39))

### Documentation

- Update readme with picture
  ([`576c0cd`](https://github.com/Kitware/SiteView/commit/576c0cd9024c768100a2b5b9fb3d5cf1b657014e))


## v1.0.0 (2026-07-23)

- Initial Release

## v1.0.0 (2026-07-15)

- Initial Release
