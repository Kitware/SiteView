# CHANGELOG

<!-- version list -->

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
