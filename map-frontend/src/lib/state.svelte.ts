export class Position {
    #lat = $state(48.195054006407318)
    #lon = $state(16.323227502059549)

    #bearing = $state(0)
    #pitch = $state(0)

    get lat() {
        return this.#lat
    }

    get lon() {
        return this.#lon
    }

    get bearing() {
        return this.#bearing
    }
    get yaw() {
        return this.#bearing
    }

    get pitch() {
        return this.#pitch
    }

    updateLocation(lat: number, lon: number, bearing?: number) {
        this.#lat = lat
        this.#lon = lon

        if (bearing !== undefined) {
            this.#bearing = bearing;
        }
    }

    updateOrientation(bearing: number, pitch: number) {
        this.#bearing = bearing;
        this.#pitch = pitch;
    }


}

// ?16.323227502059549, 48.195054006407318