# OpenXDF

OpenXDF is a Python module built for interacting with [Open eXchange Data Format](http://openxdf.org/) files.

OpenXDF files are XML-based header files that provide all of the information necessary to interpret a signal data file. This module gives users simple methods of accessing the data stored in these documents, and helps associate the header information stored in `.xdf` files together with the raw data it's referencing.

## Table of Contents

- [Getting Started](#getting-started)
- [Usage](#usage)
- [Development](#development)
- [Credits](#credits)
- [License](#license)

## Getting Started

Currently...

1. Use `pipenv install` on the `.tar.gz` file in the releases tab.

Soon...

```$ pip install openxdf```

### Prerequisites

Currently requires Python 3.6 with `pipenv` installed.

## Usage

```python
>>> import openxdf
>>> xdf = openxdf.OpenXDF("/path/to/file/.../example.xdf")
>>> xdf.header
{"ID": "Example", "EpochLength": 30, "FrameLength": 1, "Endian": "little",
"File": "Example.rawdata"}
>>> xdf.sources
[{"SourceName": "FP1", "Unit": 1e-06, "UseGridScale": "false",
  "MinSamplingRate": 200, "MinSampleWidth": 1, "Ignore": "false",
  "PhysicalMax": 3199.9, "Signed": "true", "SampleWidth": 2,
  "SampleFrequency": 200, "DigitalMax": 32767, "DigitalMin": -32768,
  "PhysicalMin": -3200, "DigitalToVolts": 0.0976563},
  {...},
]

>>> signals = openxdf.Signal(xdf, "/path/to/file/.../example.data")
>>> signals.to_numeric(["FP1", "EOG"])
{"FP1": [[100, -10, 5, -25,...], [200, -20, 10, -50, ...]],
"EOG": [[10, -35, 25, -40,...], [65, 20, -100, -10, ...]]}
>>> signals.to_edf("/output/path/.../example.edf")
```

## Development

### Contributing

Please checkout a development branch for whatever features you want to work on.

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
