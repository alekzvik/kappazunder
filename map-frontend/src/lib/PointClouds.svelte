<script lang="ts">
    import { Deck, FirstPersonView } from "@deck.gl/core";
    import {PointCloudLayer} from '@deck.gl/layers';
    // import {COPCSource} from '@loaders.gl/copc';

    import { onMount } from "svelte";
    import { dataBucket } from "./constants";

    let deck: Deck;
    let canvas: HTMLCanvasElement;


    // const url = new URL('Sensor_11003/scandata_173.laz', dataBucket)
    const url = 'http://localhost:5173/copc/autzen-classified.copc.laz'

    let copcSource = COPCSource.createDataSource(url.toString(), {});

    const layer = new PointCloudLayer({
        id: 'point-cloud',
        data: copcSource,
        // loaders: [COPCSource],
    });

    // const layer = new Tile3DLayer({
    //     id: "3dtiles",
    //     // Tileset json file url
    //     data: new URL("3dtiles/tileset.json", dataBucket),
    //     loader: Tiles3DLoader,
    //     // loadOptions: {
    //     //     // Set up Ion account: https://cesium.com/docs/tutorials/getting-started/#your-first-app
    //     //     'cesium-ion': {accessToken: '<ion_access_token_for_your_asset>'}
    //     // },
    //     onTilesetLoad: (tileset: Tileset3D) => {
    //         // Recenter to cover the tileset
    //         const { cartographicCenter, zoom } = tileset;
    //         if (cartographicCenter)
    //             deck.setProps({
    //                 initialViewState: {
    //                     longitude: cartographicCenter[0],
    //                     latitude: cartographicCenter[1],
    //                     zoom,
    //                 },
    //             });
    //     },
    //     pointSize: 2,
    // });

    const firstPersonView = new FirstPersonView()

    onMount(() => {
        deck = new Deck({
            canvas: canvas,
            initialViewState: {
                latitude: 48,
                longitude: 16,
                zoom: 16
            },
            controller: true,
            // views: firstPersonView,
            layers: [layer],
            width: 1000,
            height: 1000,
        });

        return () => {};
    });
</script>

<canvas id="deck" bind:this={canvas}> </canvas>

<style>
    #deck {
        height: 100%;
        width: 100%;
    }
</style>
