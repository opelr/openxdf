# OpenXDF

Processing exported Polysmith PSG files in OpenXDF format.

This repository contains scripts that assist with batch processing [Polysmith](http://www.nihonkohden.de/products/neurology/eeg/polysomnography/polysmith.html?L=1) overnight sleep studies (PSG) from the sleep clinic.

These functions process decrpyted OpenXDF files -- this library contains functions which will ensure file deidentification, grab sleep tech comments, and save XDF files as JSONs to save space. Files are then loaded again and sleep staging/scoring information is scraped for each study.


## Table of Contents

- [Getting Started](#getting-started)
- [Usage](#usage)
- [Development](#development)
- [Credits](#credits)
- [License](#license)

## Getting Started

1. Clone or download the repository to your local machine.
2. Use `pipenv install` on the `.tar.gz` file in the `dist` folder.

### Prerequisites

Requires Python with `pipenv` installed.

## Usage

1. ...
2. ...
3. ...

## Development

Instructions for development and contributing

### Contributing

Please checkout a development branch for whatever features you want to work on.

Run `make package-dist` to 

### Running Tests

#### Functional Tests

`make dev-tests`

#### Style Tests

`make dev-format`

### Versioning

Our group uses [Semantic Versioning](http://semver.org/) for versioning.

## Credits

### Authors

- Ryan Opel

## License

This project is licensed under the GNU General Public License v2.0 - see [LICENSE](LICENSE) for details.