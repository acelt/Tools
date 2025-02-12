library(httr)

key <- 'AIzaSyCy2UpWNW-Fcb0eGUMpbNxPZ7d9kqOp1c0'

geojson <- '{
  "type": "Feature",
  "geometry": {
    "geodesic": false,
    "type": "Polygon",
    "coordinates": [
      [
        [
          -107.97841585512226,
          47.138538781986426
        ],
        [
          -107.69277132387226,
          47.138538781986426
        ],
        [
          -107.69277132387226,
          47.29710732884726
        ],
        [
          -107.97841585512226,
          47.29710732884726
        ],
        [
          -107.97841585512226,
          47.138538781986426
        ]
      ]
    ]
  },
  "properties": {"mask": true, "year": null}
}
'

foo <- POST("https://rap-api-public-cn7y68wn.uc.gateway.dev/v1/cover", 
            query = list(key = key), content_type_json(), body = geojson_bb)
content(foo, "text")
# content(foo, "parsed")
