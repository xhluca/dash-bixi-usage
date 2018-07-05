import dash_core_components as dcc
import dash_html_components as html
import numpy as np

import plotly.graph_objs as go


# Display utility functions
def _merge(a, b):
    return dict(a, **b)


def _omit(omitted_keys, d):
    return {k: v for k, v in d.items() if k not in omitted_keys}


# Custom Display Components
def Card(children, **kwargs):
    return html.Section(
        children,
        style=_merge({
            'padding': 20,
            'margin': 5,
            'borderRadius': 5,
            'border': 'thin lightgrey solid',
            #
            # # Remove possibility to select the text for better UX
            # 'user-select': 'none',
            # '-moz-user-select': 'none',
            # '-webkit-user-select': 'none',
            # '-ms-user-select': 'none'
        }, kwargs.get('style', {})),
        **_omit(['style'], kwargs)
    )


def NamedSlider(name, **kwargs):
    return html.Div(
        style={'margin': '25px 27px 35px 4px'},
        children=[
            html.P(f'{name}:'),
            html.Div(
                style={'margin-left': '6px'},
                children=dcc.Slider(**kwargs)
            )
        ]
    )


def NamedInlineRadioItems(name, short, options, val, **kwargs):
    return html.Div(
        id=f'div-{short}',
        style=_merge({
            'display': 'block'
        }, kwargs.get('style', {})),
        children=[
            f'{name}:',
            dcc.RadioItems(
                id=f'radio-{short}',
                options=options,
                value=val,
                labelStyle={
                    'display': 'inline-block',
                    'margin-right': '7px',
                    'font-weight': 300
                },
                style={
                    'display': 'inline-block',
                    'margin-left': '7px'
                }
            )
        ],
        **_omit(['style'], kwargs)
    )


def NamedDropdown(name, **kwargs):
    return html.Div(
        style={'margin': '10px 0px'},
        children=[
            html.P(
                children=f'{name}:',
                style={'margin-left': '3px'}
            ),

            dcc.Dropdown(**kwargs)
        ]
    )
