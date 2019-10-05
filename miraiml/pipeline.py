"""
:mod:`miraiml.pipeline` contains a function that lets you build your own
pipeline classes and a few pre-defined pipelines for baselines.
"""

from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LinearRegression

from miraiml.util import is_valid_pipeline_name
from miraiml.core import BasePipelineClass


def compose(steps):
    """
    A function that can be used to define pipeline classes dinamically. Builds a
    pipeline class that can be instantiated with particular parameters for each
    of its transformers/estimator without needing to call ``set_params`` as you
    would do with scikit-learn's Pipeline when performing hyperparameters
    optimizations.

    Similarly to scikit-learn's Pipeline, ``steps`` is a list of tuples
    containing an alias and the respective pipeline element. Although, since
    this function is a class factory, you shouldn't instantiate the
    transformer/estimator as you would do with scikit-learn's Pipeline. Thus,
    this is how :func:`compose` should be called:

    ::

        >>> from sklearn.ensemble import RandomForestClassifier
        >>> from sklearn.preprocessing import StandardScaler

        >>> from miraiml.pipeline import compose

        >>> MyPipelineClass = compose(
        ...     steps = [
        ...         ('scaler', StandardScaler), # StandardScaler instead of StandardScaler()
        ...         ('rfc', RandomForestClassifier) # No instantiation either
        ...     ]
        ... )

    And then, in order to instantiate ``MyPipelineClass`` with the desired
    parameters, you just need to refer to them as a concatenation of their
    respective class aliases and their names, separated by ``'__'``.

    ::

        >>> pipeline = MyPipelineClass(scaler__with_mean=False, rfc__max_depth=3)

    If you want to know which parameters you're allowed to play with, just call
    :func:`get_params`:

    ::

        >>> params = pipeline.get_params()
        >>> print("\\n".join(params))
        scaler__with_mean
        scaler__with_std
        rfc__bootstrap
        rfc__class_weight
        rfc__criterion
        rfc__max_depth
        rfc__max_features
        rfc__max_leaf_nodes
        rfc__min_impurity_decrease
        rfc__min_impurity_split
        rfc__min_samples_leaf
        rfc__min_samples_split
        rfc__min_weight_fraction_leaf
        rfc__n_estimators
        rfc__n_jobs
        rfc__oob_score
        rfc__random_state
        rfc__verbose
        rfc__warm_start

    You can check the available methods for your instantiated pipelines on the
    documentation for :class:`miraiml.core.BasePipelineClass`, which is the
    class from which the composed classes inherit from.

    **The intended purpose** of such pipeline classes is that they can work as
    base models to build instances of :class:`miraiml.HyperSearchSpace`.

    ::

        >>> from miraiml import HyperSearchSpace

        >>> hyper_search_space = HyperSearchSpace(
        ...     model_class=MyPipelineClass,
        ...     id='MyPipelineClass',
        ...     parameters_values=dict(
        ...         scaler__with_mean=[True, False],
        ...         scaler__with_std=[True, False],
        ...         rfc__max_depth=[3, 4, 5, 6]
        ...     )
        ... )

    :type steps: list
    :param steps: The list of pairs (alias, class) to define the pipeline.

        .. warning::
            Repeated aliases are not allowed and none of the aliases can start
            with numbers or contain ``'__'``.

            The classes used to compose a pipeline **must** implement ``get_params``
            and ``set_params``, such as scikit-learn's classes, or :func:`compose`
            **will break**.

    :rtype: type
    :returns: The composed pipeline class

    :raises: ``ValueError``, ``TypeError``, ``NotImplementedError``
    """

    aliases = []

    for alias, class_type in steps:
        if not isinstance(alias, str):
            raise TypeError('{} is not a string'.format(alias))

        if not is_valid_pipeline_name(alias):
            raise ValueError('{} is not allowed for an alias'.format(alias))

        class_content = dir(class_type)

        if 'fit' not in class_content:
            raise NotImplementedError('{} must implement fit'.format(class_type.__name__))

        aliases.append(alias)

        if len(aliases) < len(steps):
            if 'transform' not in class_content:
                raise NotImplementedError(
                    '{} must implement transform'.format(class_type.__name__)
                )
        else:
            if 'predict' not in class_content and 'predict_proba' not in class_content:
                raise NotImplementedError(
                    '{} must implement predict or predict_proba'.format(class_type.__name__)
                )

    if len(set(aliases)) != len(aliases):
        raise ValueError('Repeated aliases are not allowed')

    return type('MiraiPipeline', (BasePipelineClass,), dict(steps=steps))


__initial_steps__ = [('ohe', OneHotEncoder), ('inpute', SimpleImputer)]


class NaiveBayesBaseliner(compose(__initial_steps__ + [('naive', GaussianNB)])):
    """
    Testing doc.
    """
    def __init__(self):
        super().__init__()


class LinearRegressionBaseliner(compose(__initial_steps__ + [('linear', LinearRegression)])):
    """
    Testing doc.
    """
    def __init__(self):
        super().__init__()
