<script lang="ts">
  /// <reference types="@types/geojson" />
  import { onMount } from "svelte";
  import * as maplibregl from "maplibre-gl";
  import "maplibre-gl/dist/maplibre-gl.css";
  import { Protocol, PMTiles } from "pmtiles";
  import type { FeatureCollection, Point } from "@types/geojson";

  import type { Position } from "./state.svelte";
  import triangle from "./triangle";

  interface Props {
    position: Position;
  }

  let { position }: Props = $props();

  let map: maplibregl.Map;

  let protocol = new Protocol();
  maplibregl.addProtocol("pmtiles", protocol.tile);
  const PMTILES_URL =
    "https://pub-cde3253d20044d0484f84404e6716a33.r2.dev/pmtiles/images_merged.pmtiles";

  const p = new PMTiles(PMTILES_URL);
  protocol.add(p);

  interface PositionProps {
    bearing: number;
  }
  const geojson: FeatureCollection<Point, PositionProps> = {
    type: "FeatureCollection",
    features: [],
  };

  $effect(() => {
    geojson.features = [
      {
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [position.lon, position.lat],
        },
        properties: {
          bearing: position.bearing,
        },
      },
    ];
    map &&
      (map.getSource("point") as maplibregl.GeoJSONSource).setData(geojson);
  });

  onMount(() => {
    p.getHeader().then((h) => {
      map = new maplibregl.Map({
        container: "map",
        zoom: h.maxZoom - 2,
        center: [h.centerLon, h.centerLat],
        style: "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
      });

      map.on("load", () => {
        map.addSource('temp-raster-tiles', {
          'type': 'raster',
          'tiles': [
            "http://127.0.0.1:8000/stac/tiles/WebMercatorQuad/{z}/{x}/{y}?url=https://raw.githubusercontent.com/stac-extensions/render/65edf9bcc7dfe0a02e0191a277c1ac81d86b698e/examples/item-landsat8.json&assets=ndvi&resampling_method=average&colormap_name=ylgn"
          ]
        })
        map.addLayer({
          'id': 'simple-tiles',
          'type': 'raster',
          'source': 'temp-raster-tiles',
          'minzoom': 0,
          'maxzoom': 22
        })
        map.addSource("pmtiles-vector", {
          type: "vector",
          url: `pmtiles://${PMTILES_URL}`,
          attribution:
            'Data source: City of Vienna - <a href="https://data.wien.gv.at">data.wien.gv.at</a>',
        });
        map.addLayer({
          id: "images",
          source: "pmtiles-vector",
          "source-layer": "images_merged",
          type: "circle",
          paint: {
            "circle-opacity": 0.7,
            "circle-color": [
              "case",
              ["boolean", ["get", "has_images"], false],
              "#4daa4d",
              "#ff4d4d",
            ],
            "circle-radius": [
              "case",
              ["boolean", ["get", "has_images"], false],
              7,
              5,
            ],
          },
        });
        map.addSource("point", {
          type: "geojson",
          data: geojson,
        });

        map.addImage("triangle", triangle);
        map.addLayer({
          id: "point-direction",
          type: "symbol",
          source: "point",
          layout: {
            "symbol-placement": "point",
            "icon-anchor": "top-left",
            "icon-image": "triangle",
            "icon-rotate": ["-", ["*", ["get", "bearing"], 180 / Math.PI], 135],
            "icon-rotation-alignment": "map",
          },
        });
        map.addLayer({
          id: "point",
          type: "circle",
          source: "point",
          paint: {
            "circle-radius": 10,
            "circle-color": "#3887be",
          },
        });

        map.on("click", "images", (e: maplibregl.MapLayerMouseEvent) => {
          if (e.features) {
            const feature = e.features[0];
            if (feature.properties["has_images"]) {
              const geometry = feature.geometry as Point;
              let [lon, lat] = geometry.coordinates;
              console.log(feature);
              position.updateLocation(lat, lon);
            }
          }
        });

        // Change the cursor to a pointer when the mouse is over the images layer.
        map.on("mouseenter", "images", (e: maplibregl.MapLayerMouseEvent) => {
          if (e.features.length > 0) {
            const feature = e.features[0];
            map.getCanvas().style.cursor = "pointer";
          }
        });

        // Change it back to a pointer when it leaves.
        map.on("mouseleave", "images", () => {
          map.getCanvas().style.cursor = "";
        });
      });
    });
    return () => {
      map.remove();
    };
  });
</script>

<div id="map"></div>

<style>
  #map {
    height: 100%;
  }
</style>
