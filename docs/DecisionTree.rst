Decision Tree
=============

Class Reference
---------------

.. autoclass:: pykitml.DecisionTree
    
    .. automethod:: __init__

    .. automethod:: feed

    .. automethod:: get_output

    .. automethod:: get_output_onehot

    .. automethod:: train

    .. automethod:: accuracy

    .. automethod:: confusion_matrix

    .. automethod:: r2score

    .. automethod:: show_tree

Example: Classifying Iris
-------------------------

**Dataset**

:ref:`iris_dataset`

**Training**

.. literalinclude:: ../tests/test_iris_tree.py
   :pyobject: test_iris_tree
   :lines: 3-
   :end-before: # Assert
   :dedent: 4

**Predict type of species with sepal-length, sepal-width, petal-length, petal-width: 
5.8, 2.7, 3.9, 1.2**

.. literalinclude:: ../tests/test_iris_tree.py
   :pyobject: test_predict_iris_tree
   :lines: 3-
   :dedent: 4

**Tree Graph**

.. image:: ./demo_pics/tree.png

**Confusion Matrix**

.. image:: ./demo_pics/tree_confusion_matrix.png