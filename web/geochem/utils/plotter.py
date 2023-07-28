"""Contains a class that handles visualisations of analysis."""

from typing import Tuple
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('agg')
import matplotlib.cm as cm
from matplotlib import pyplot as plt
from scipy.cluster.hierarchy import dendrogram
from scipy.cluster.hierarchy import set_link_color_palette
from sklearn.metrics import silhouette_samples

from . import exceptions
from . import data_utils

# Define some colours for the plot themes
COPPER = '#C77C53'
COPPER2 = '#170E09'


class Plotter:
    """
    Handles visualisation creation directly of the data in a datacleaner,
    and of the analysis done in the analyser.

    Attributes:
        analyser: The Analyser that will be interpreted.
        logger: The logger to record events.
    """

    def __init__(self, analyser):
        """Create a plotter"""
        self.analyser = analyser

    def plot_means(self, filename: str, figsize: Tuple[int,int]=(10,10),
            label_font_size: int=16, title_font_size: int=24, rotation: int=0,
            colour: str=COPPER):
        """Plots the means of each column.

        Args:
            filename: The filename to save the plot to.
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the points in the plot.
        """

        if self.analyser.summaries is None:
            raise exceptions.ModelNotTrainedError('Stat Summaries')

        # Get summaries locally for easier access
        summaries = self.analyser.summaries

        # Get means
        means = {}
        for summary in summaries:
            try:
                means[summary] = summaries[summary]['mean']
            except KeyError:
                pass

        plt.figure(figsize=figsize)

        # Plot creation
        plt.scatter(range(len(means.values())), means.values(), color=colour)
        plt.xticks(range(len(means.keys())), means.keys(), 
                fontsize=label_font_size, rotation=rotation)
        
        # Title and axis label
        plt.title('Mean of Each Column', fontsize=title_font_size)
        plt.ylabel('Mean', fontsize=label_font_size)

        plt.savefig(filename)

        plt.close()

    def plot_medians(self, filename: str, figsize: Tuple[int,int]=(10,10),
            label_font_size: int=16, title_font_size: int=24, rotation: int=0,
            colour: str=COPPER):
        """Plots the medians of each column.

        Args:
            filename: The filename to save the plot to.
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the points in the plot.
        """

        if self.analyser.summaries is None:
            raise exceptions.ModelNotTrainedError('Stat Summaries')

        # Get summaries locally for easier access
        summaries = self.analyser.summaries

        # Get medians
        medians = {}
        for summary in summaries:
            try:
                medians[summary] = summaries[summary]['50%']
            except KeyError:
                pass

        plt.figure(figsize=figsize)

        # Plot creation
        plt.scatter(range(len(medians.values())), medians.values(), 
                color=colour)
        plt.xticks(range(len(medians.keys())), medians.keys(),
                fontsize=label_font_size, rotation=rotation)

        # Title and axis label
        plt.title('Median of Each Column', fontsize=title_font_size)
        plt.ylabel('Median', fontsize=label_font_size)

        plt.savefig(filename)

        plt.close()

    def plot_std(self, filename: str, figsize: Tuple[int,int]=(10,10), 
            label_font_size: int=16, title_font_size: int=24, rotation: int=0, 
            colour: str=COPPER):
        """Plots the standard deviation of each column.

        Args:
            filename: The filename to save the plot to.
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the points in the plot.
        """

        if self.analyser.summaries is None:
            raise exceptions.ModelNotTrainedError('Stat Summaries')

        # Get summaries locally for easier access
        summaries = self.analyser.summaries

        stds = {}
        for summary in summaries:
            try:
                stds[summary] = summaries[summary]['std']
            except KeyError:
                pass
            

        plt.figure(figsize=figsize)

        # Plot creation
        plt.scatter(range(len(stds.values())), stds.values(), color=colour)
        plt.xticks(range(len(stds.keys())), stds.keys(), 
                fontsize=label_font_size, rotation=rotation)

        # Title and axis label
        plt.title('Standard Deviation of Each Column', 
                fontsize=title_font_size)
        plt.ylabel('Standard Deviation', fontsize=label_font_size)

        plt.savefig(filename)

        plt.close()

    def plot_range(self, filename: str, figsize: Tuple[int,int]=(10,10), 
            label_font_size: int=16, title_font_size: int=24, rotation: int=0, 
            colour: Tuple[str,str]=(COPPER, COPPER2)):
        """Plots the min and max of each column.

        Args:
            filename: The filename to save the plot to.
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the points in the plot.
        """
        
        if self.analyser.summaries is None:
            raise exceptions.ModelNotTrainedError('Stat Summaries')

        # Get summaries locally for easier access
        summaries = self.analyser.summaries

        mins = {}
        maxes = {}
        for summary in summaries: 
            try:
                mins[summary] = summaries[summary]['min']
                maxes[summary] = summaries[summary]['max']
            except KeyError:
                pass

        plt.figure(figsize=figsize)

        # Plot creation
        plt.scatter(range(len(mins.values())), mins.values(), color=colour[1])
        plt.scatter(range(len(maxes.values())), maxes.values(), 
                color=colour[0])
        plt.xticks(range(len(mins.keys())), mins.keys(), 
                fontsize=label_font_size, rotation=rotation)

        # Title
        plt.title('Range of Each Column', 
                fontsize=title_font_size)

        # Legend
        plt.legend(['Min', 'Max'])

        plt.savefig(filename)

        plt.close()

    def plot_box_whisker(self, filename: str, figsize: Tuple[int,int]=(10,10), 
            label_font_size: int=16, title_font_size: int=24, rotation: int=0,
            horizontal: bool=True, subset_X: list=None):
        """Plots a box and whisker plot for an individual column.
        Args:
            filename: The filename to save the plot to.
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            horizontal: The align of the plot.
            subset_X: The selected columns
        """
        if self.analyser.summaries is None:
            raise exceptions.ModelNotTrainedError('Stat Summaries')
        
        # Create data for plot
        if subset_X is None:
            subset_X = [col for col in self.analyser.dataframe.columns]

        # Remove categorical data column from subset_X
        subset_X = data_utils.check_list_datatype(
            self.analyser.dataframe, subset_X, 'object', False)

        # Create data for plot
        box_data = self.analyser.dataframe[subset_X]

        # Select align
        if horizontal:
            #Set size
            plt.figure(figsize=figsize)

            # Plot the importances
            plt.boxplot(box_data,vert=False)

            # Set ytick
            plt.yticks(range(1,len(subset_X)+1), subset_X,
                rotation=rotation, fontsize=label_font_size)
           
            # Boxplot title
            plt.title('Boxplot', fontsize=title_font_size)

        else:
            #Set size
            plt.figure(figsize=figsize)

            # Plot the importances
            plt.boxplot(box_data,vert=True)

            # Set labels
            plt.xticks(range(1,len(subset_X)+1), subset_X, 
                rotation=rotation, fontsize=label_font_size)

            # Boxplot title
            plt.title('Boxplot', fontsize=title_font_size)

        plt.tight_layout()

        plt.savefig(filename)

        plt.close()

    def plot_violin(self, filename: str, figsize: Tuple[int,int]=(10,10),
            label_font_size: int=16, title_font_size: int=24, rotation: int=0,
            horizontal: bool=True, subset_X: list=None):
        """Plots the violin of each column.

         Args:
            filename: The filename to save the plot to.
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            horizontal: The align of the plot.
            subset_X: The selected columns
        """
        
        if self.analyser.summaries is None:
            raise exceptions.ModelNotTrainedError('Stat Summaries')

        if subset_X is None:
            subset_X = [col for col in self.analyser.dataframe.columns]

        # Remove categorical data column from subset_X
        subset_X = data_utils.check_list_datatype(
            self.analyser.dataframe, subset_X, 'object', False)
        
        plt.figure(figsize=figsize)
        
        if horizontal:
            
            plt.violinplot([self.analyser.dataframe[col]
                for col in subset_X], vert=False)
        
            plt.yticks(np.arange(1, len(subset_X) + 1), subset_X, 
                fontsize=label_font_size, rotation=rotation)
        
        
            plt.xlabel('Distribution', fontsize=label_font_size)
        
        else:
            
            plt.violinplot([self.analyser.dataframe[col]
                for col in subset_X])
        
            plt.xticks(np.arange(1, len(subset_X) + 1), subset_X, 
                fontsize=label_font_size, rotation=rotation)
        
        
            plt.ylabel('Distribution', fontsize=label_font_size)
        
        plt.title('Violin Plot of Each Column', fontsize=title_font_size)
        
        plt.tight_layout()
        
        plt.savefig(filename)

        plt.close()

    # METHODS BELOW ARE ALL CURRENTLY UNUSED

    def visualise_empty_cells(self, filename: str, 
            figsize: Tuple[int,int]=(10,10), label_font_size: int=16,
            title_font_size: int=24, rotation: int=0, colour: str=COPPER):
        """Creates a scatter plot visualising empty cells.
        
        Args:
            filename: The filename to save the plot to.
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the bars in the plot.
        """

        # Check stats have been called
        if self.analyser.stats is None:
            raise exceptions.ModelNotTrainedError('Data Statistics')

        # Plot each column
        plt.figure(figsize=figsize)
        for index in range(len(self.analyser.dataframe.columns)):
            plt.scatter(index, 
                    self.analyser.stats['empty_cells_per_column'][index],
                    color=colour)

        names = self.analyser.dataframe.columns

        plt.title("Missing Values", fontsize=title_font_size)
        
        plt.xticks(range(len(self.analyser.dataframe.columns)), 
                labels=names, rotation=rotation, fontsize=label_font_size)

        plt.savefig(filename)
        plt.close()

    def visualise_empty_cells_bar(self, filename: str, 
            figsize: Tuple[int,int]=(10,10), label_font_size: int=16,
            title_font_size: int=24, rotation: int=0, colour: str=COPPER):
        """Creates a bar graph visualising empty cells.
        
        Args:
            filename: The filename to save the plot to.
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the bars in the plot.
        """

        # Check stats have been called
        if self.analyser.stats is None:
            raise exceptions.ModelNotTrainedError('Data Statistics')

        # Plot each column
        plt.figure(figsize=figsize)
        
        plt.bar(range(len(
                    self.analyser.stats['empty_cells_per_column'].keys())), 
                height=self.analyser.stats['empty_cells_per_column'].values(),
                color=colour)

        names = self.analyser.dataframe.columns

        plt.title("Missing Values", fontsize=title_font_size)
        
        plt.xticks(range(len(self.analyser.dataframe.columns)), 
                labels=names, rotation=rotation, fontsize=label_font_size)

        plt.savefig(filename)
        plt.close()

    def plot_2d_comparison_kmeans(self, col1: str, col2: str, filename: str,
            plot_centres: bool=True, 
            colours: list=['k', 'r', 'b', 'c']) -> None:
        """Plots a two dimensional slice of the clustered data.

        Args:
            col1: The header of the first dimension to plot.
            col2: The header of the second dimension to plot.
            filename: The name of the file to save the plot to.
            plot_centres: If True, also plots the 2D slice of the cluster
              centre.
            colours: The list of colours for different clusters to use.
        """
        # Log start

        # Check that there is kmeans to plot on
        if self.analyser.kmeans is None:
            raise exceptions.ModelNotTrainedError('K-means')

        # Get data for the two dimensions being compared
        data_x = self.analyser.dataframe[col1]
        data_y = self.analyser.dataframe[col2]

        cluster_colours = [colours[i] for i in self.analyser.kmeans.labels_]

        # Plot them against each other
        plt.scatter(data_x, data_y, c=cluster_colours)

        cluster_index_x = self.analyser.dataframe.columns.get_loc(col1)
        cluster_index_y = self.analyser.dataframe.columns.get_loc(col2)

        # Plot the centres
        if plot_centres:
            for i in range(self.analyser.k):
                cluster_x = self.analyser.kmeans.cluster_centers_[i][
                    cluster_index_x]
                cluster_y = self.analyser.kmeans.cluster_centers_[i][
                    cluster_index_y]

                plt.scatter(cluster_x, cluster_y, c=colours[i], marker='*')

        # Set the labels for the axes
        #plt.xlabel('{} ({})'.format(col1, self.analyser.datacleaner.units))
        #plt.ylabel('{} ({})'.format(col2, self.analyser.datacleaner.units))
        plt.xlabel('{}'.format(col1))
        plt.ylabel('{}'.format(col2))

        # Save the image
        plt.savefig(filename)

        plt.close()

        # Log success

    def plot_silhouette(self, filename: str, spectral_colour: bool=True,
            figsize: Tuple[int,int]=(10,10), label_font_size: int=16,
            title_font_size: int=24):
        """Creates a silhouette plot for k means.
        
        Args:
            filename: The name of the file to save the plot to.
            spectral_colour: If True, uses matplotlib to choose a new colour
              per cluster.
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
        """
        # Check that there is kmeans to plot on
        if self.analyser.kmeans is None:
            raise exceptions.ModelNotTrainedError('K-means')

        subset_X = data_utils.check_list_datatype(
                self.analyser.dataframe, 
                self.analyser.dataframe.columns, 'object', False)

        # TODO Add this to analyser instead
        # Compute the silhouette scores for each sample
        sil_values = silhouette_samples(
                        self.analyser.dataframe[subset_X],
                        self.analyser.kmeans.labels_)

        plt.figure(figsize=figsize)
        
        # Create the plot
        y_lower = 10
        for k in range(len(self.analyser.kmeans.cluster_centers_)):
            kth_cluster_sil_values = \
                    sil_values[self.analyser.kmeans.labels_ == k]

            kth_cluster_sil_values.sort()

            size_cluster_k = kth_cluster_sil_values.shape[0]
            y_upper = y_lower + size_cluster_k

            # Choose colour
            if spectral_colour:
                colour = cm.nipy_spectral(k / \
                        len(self.analyser.kmeans.cluster_centers_))
            else:
                colour = COPPER

            plt.fill_betweenx(np.arange(y_lower, y_upper),
                          0, kth_cluster_sil_values,
                          facecolor=colour, edgecolor=colour, alpha=0.7)

            # Label for clusters, could cause issues with large
            plt.text(-0.05, y_lower + 0.5 * size_cluster_k, str(k))

            y_lower = y_upper + 10

        # Adjust labels
        plt.title("Silhouette Plot of Clusters", fontsize=title_font_size)
        plt.xlabel("Silhouette coefficient values", fontsize=label_font_size)
        plt.ylabel("Cluster label", fontsize=label_font_size)
        plt.yticks([])

        # Save the figure
        plt.savefig(filename)

        plt.close()
        
    def plot_rf_importances(self, filename: str, ordered: bool=True, 
            big_to_small: bool=True, horizontal: bool=True, 
            figsize: Tuple[int,int]=(10,10), label_font_size: int=16,
            title_font_size: int=24, rotation: int=0, 
            colour: str=COPPER) -> None:
        """
        Plots the importance of each feature in a pre-run random forest. 
        
        Args:
            filename: The filename to save the plot to.
            ordered: Whether or not to sort the importances in ascending order
            big_to_small: If ordered is True, this indicates whether the plot
              should be in ascending or descending order.
            horizontal: If True, plots a horizontal bar graph. Otherwise,
              a normal bar graph (vertical) is created
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the bars in the plot.
        """

        # Log start

        # Check that there is an rf to get the importances of, also covers the
        # target column set.
        if self.analyser.rf is None:
            raise exceptions.ModelNotTrainedError('Random Forest')
        
        # Get the importances
        importances = self.analyser.rf.feature_importances_

        # Sort if necessary
        if ordered:
            if big_to_small:
                index_sorted = np.argsort(importances)[::-1]
                importances = np.sort(importances)[::-1]

            else:
                index_sorted = np.argsort(importances)
                importances = np.sort(importances)
        else:
            index_sorted = [i for i in range(len(importances))]
            
        if self.analyser.rf_subset_X is None:
            labels = [self.analyser.dataframe.columns[i] 
                    for i in index_sorted]
        else:
            labels = [self.analyser.rf_subset_X[i] for i in index_sorted]

        # Create figure and initialise with figure size
        plt.figure(figsize=figsize)

        if horizontal:
            # Plot the importances
            plt.barh(range(self.analyser.rf_num_predictors), 
                    importances, color=colour)

            # Set labels
            plt.yticks(ticks=range(self.analyser.rf_num_predictors), 
                    labels=labels, rotation=rotation, fontsize=label_font_size)

            plt.title("Importances Random Forest Predicting {}".format(
                    self.analyser.rf_target_column), fontsize=title_font_size)

        else:
            # Plot the importances
            plt.bar(range(self.analyser.rf_num_predictors), importances, 
                    color=colour)

            # Set labels
            plt.xticks(range(self.analyser.rf_num_predictors), labels,
                    rotation=rotation, fontsize=label_font_size)

            plt.title("Importances Random Forest Predicting {}".format(
                    self.analyser.rf_target_column), fontsize=title_font_size)


        # Save the figure
        plt.savefig(filename)

        plt.close()

    def plot_rf_importances_big_10(self, filename: str, ordered: bool = True,
                            big_to_small: bool = True, horizontal: bool = True,
                            figsize: Tuple[int, int] = (10, 10), label_font_size: int = 16,
                            title_font_size: int = 24, rotation: int = 0,
                            colour: str = COPPER) -> None:
        """
        Plots the importance of each feature in a pre-run random forest.

        Args:
            filename: The filename to save the plot to.
            ordered: Whether or not to sort the importances in ascending order
            big_to_small: If ordered is True, this indicates whether the plot
              should be in ascending or descending order.
            horizontal: If True, plots a horizontal bar graph. Otherwise,
              a normal bar graph (vertical) is created
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the bars in the plot.
        """

        # Log start

        # Check that there is an rf to get the importances of, also covers the
        # target column set.
        if self.analyser.rf is None:
            raise exceptions.ModelNotTrainedError('Random Forest')

        # Get the importances
        importances = self.analyser.rf.feature_importances_

        # Sort if necessary
        if ordered:
            if big_to_small:
                index_sorted = np.argsort(importances)[::-1]
                importances = np.sort(importances)[::-1]

            else:
                index_sorted = np.argsort(importances)
                importances = np.sort(importances)
        else:
            index_sorted = [i for i in range(len(importances))]

        if self.analyser.rf_subset_X is None:
            labels = [self.analyser.dataframe.columns[i]
                      for i in index_sorted]
        else:
            labels = [self.analyser.rf_subset_X[i] for i in index_sorted]

        if len(importances) >= 10 and len(labels) >= 10:
            labels = labels[-10:]
            importances = importances[-10:]
        else:
            return False

        # Create figure and initialise with figure size
        plt.figure(figsize=figsize)

        if horizontal:
            # Plot the importances
            plt.barh(range(10),
                     importances, color=colour)

            # Set labels
            plt.yticks(ticks=range(10),
                       labels=labels, rotation=rotation, fontsize=label_font_size)

            plt.title("Biggest 10 Importances Random Forest Predicting {}".format(
                self.analyser.rf_target_column), fontsize=title_font_size)

        else:
            # Plot the importances
            plt.bar(range(10), importances,
                    color=colour)

            # Set labels
            plt.xticks(range(10), labels,
                       rotation=rotation, fontsize=label_font_size)

            plt.title("Biggest 10 Importances Random Forest Predicting {}".format(
                self.analyser.rf_target_column), fontsize=title_font_size)

        # Save the figure
        plt.savefig(filename)

        plt.close()

    def plot_rf_importances_small_10(self, filename: str, ordered: bool = True,
                                       big_to_small: bool = True, horizontal: bool = True,
                                       figsize: Tuple[int, int] = (10, 10), label_font_size: int = 16,
                                       title_font_size: int = 24, rotation: int = 0,
                                       colour: str = COPPER) -> None:
            """
            Plots the importance of each feature in a pre-run random forest.

            Args:
                filename: The filename to save the plot to.
                ordered: Whether or not to sort the importances in ascending order
                big_to_small: If ordered is True, this indicates whether the plot
                  should be in ascending or descending order.
                horizontal: If True, plots a horizontal bar graph. Otherwise,
                  a normal bar graph (vertical) is created
                figsize: The size in which to create the figure.
                label_font_size: The font size of axis labels.
                title_font_size: The font size of title.
                rotation: The rotation of the tick labels.
                colour: The colour of the bars in the plot.
            """

            # Log start

            # Check that there is an rf to get the importances of, also covers the
            # target column set.
            if self.analyser.rf is None:
                raise exceptions.ModelNotTrainedError('Random Forest')

            # Get the importances
            importances = self.analyser.rf.feature_importances_

            # Sort if necessary
            if ordered:
                if big_to_small:
                    index_sorted = np.argsort(importances)[::-1]
                    importances = np.sort(importances)[::-1]

                else:
                    index_sorted = np.argsort(importances)
                    importances = np.sort(importances)
            else:
                index_sorted = [i for i in range(len(importances))]

            if self.analyser.rf_subset_X is None:
                labels = [self.analyser.dataframe.columns[i]
                          for i in index_sorted]
            else:
                labels = [self.analyser.rf_subset_X[i] for i in index_sorted]

            if len(importances) >= 10 and len(labels) >= 10:
                labels = labels[:10]
                importances = importances[:10]
            else:
                return False

            # Create figure and initialise with figure size
            plt.figure(figsize=figsize)

            if horizontal:
                # Plot the importances
                plt.barh(range(10),
                         importances, color=colour)

                # Set labels
                plt.yticks(ticks=range(10),
                           labels=labels, rotation=rotation, fontsize=label_font_size)

                plt.title("Least 10 Importances Random Forest Predicting {}".format(
                    self.analyser.rf_target_column), fontsize=title_font_size)

            else:
                # Plot the importances
                plt.bar(range(10), importances,
                        color=colour)

                # Set labels
                plt.xticks(range(10), labels,
                           rotation=rotation, fontsize=label_font_size)

                plt.title("Least 10 Importances Random Forest Predicting {}".format(
                    self.analyser.rf_target_column), fontsize=title_font_size)

            # Save the figure
            plt.savefig(filename)

            plt.close()

    def plot_pca_feature_bar(self, filename: str,
            figsize: Tuple[int,int]=(10,10), label_font_size: int=16, 
            title_font_size: int=24, rotation: int=0, 
            colour: str=COPPER) -> None:
        """Plots features with their importance from a PCA.
        
        Args:
            filename: The filename to save the plot to.
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the bars in the plot.
        """
        # Log start

        # Check there is a PCA
        if self.analyser.pca is None:
            raise exceptions.ModelNotTrainedError(
                    'Principal Component Analysis')
        
        # Get the explained variance ratio from the PCA
        explained_var_ratio = self.analyser.pca.explained_variance_ratio_

        # Create figure and initialise with figure size
        plt.figure(figsize=figsize)

        # Plot the bar graph
        plt.barh(range(len(explained_var_ratio)), np.flip(explained_var_ratio), 
                color=colour)

        plt.yticks(ticks=range(len(explained_var_ratio)), 
                rotation=rotation, fontsize=label_font_size)

        plt.ylabel('Principal Component', fontsize=label_font_size)
        plt.xlabel('Proportion Explained Variance', fontsize=label_font_size)

        plt.title("Explained Variance of Total Data per Feature", 
                fontsize=title_font_size)

        # Save and close the figure
        plt.savefig(filename)
        plt.close()

        # Log success

    def plot_pca_cumulative_importance(self, filename: str, 
            figsize: Tuple[int,int]=(10,10), label_font_size: int=16, 
            title_font_size: int=24, rotation: int=0,
            colour: str=COPPER) -> None:
        """Plots the cumulative explained variance of the features.
        
        Args:
            filename: The filename to save the plot to.
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the bars in the plot.
        """
        # Log start

        # Check there is a PCA
        if self.analyser.pca is None:
            raise exceptions.ModelNotTrainedError(
                    'Principal Component Analysis')

        # Create figure and initialise with figure size
        plt.figure(figsize=figsize)
        
        # Get the explained variance ratio and cumulative sum
        explained_var_ratio = self.analyser.pca.explained_variance_ratio_
        cumulative_variance = np.cumsum(explained_var_ratio)

        # Plot the figure
        plt.plot(range(len(cumulative_variance)), cumulative_variance, 
                color=colour)
        plt.title('Cumulative sum of explained variance for each feature.',
                fontsize=title_font_size)
        plt.xlabel('Principle Component', fontsize=label_font_size)
        plt.ylabel('Explained Variance', fontsize=label_font_size)
        plt.savefig(filename)
        plt.close()

        # Log success

    def plot_dendrogram(self, filename: str, labels: list, 
            figsize: Tuple[int,int]=(10,10), label_font_size: int=16, 
            title_font_size: int=24, rotation: int=0, 
            colour: list=['b', COPPER, COPPER2, 'k']) -> None:
        """Plots a dendrogram for a trained HCA.
        
        Args:
            filename: The filename to save the plot to.
            labels: A list of strings corresponding to the axis labels.
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour the different cluster thresholds.
        """
        # Log start

        # Check HCA exists
        if self.analyser.hca is None:
            raise exceptions.ModelNotTrainedError(
                    'Hierarchical Clustering Analysis')
        # Plot the dendrogram
        plt.figure(figsize=figsize)
        set_link_color_palette(colour)
        dendrogram(self.analyser.hca, labels=labels, leaf_rotation=rotation,
                leaf_font_size=label_font_size, 
                above_threshold_color=colour[-1])

        plt.title("Dendrogram of Hierarchical Clustering", 
                fontsize=title_font_size)
        plt.savefig(filename)
        plt.close()

        # Log success

    def plot_correlations_heatmap(self, filenames: list, 
            figsize: Tuple[int,int]=(10,10), cmap: str='copper_r') -> None:
        """Creates heatmaps for correlation coefficients of data.

        Args:
            filenames: The list of files to save the heatmaps to.
            figsize: The size in which to create the figure.
            cmap: The colour map to use on the heatmaps.
        """
        # Log start

        if self.analyser.correlations is None:
            raise exceptions.ModelNotTrainedError('Correlation Coefficients')
        
        counter = 0
        for correlation in self.analyser.correlations:
            plt.figure(figsize=figsize)
            plt.imshow(self.analyser.correlations[correlation], 
                    cmap=cmap, interpolation=None)
            plt.colorbar()
            plt.xticks(range(len(self.analyser.cc_subset_X)), 
                    self.analyser.cc_subset_X, rotation=90)
            plt.yticks(range(len(self.analyser.cc_subset_X)), 
                    self.analyser.cc_subset_X)
            plt.title('{}'.format(correlation))

            plt.savefig(filenames[counter])
            plt.close()
            counter += 1

    def plot_single_element_correlations(self, target: str, filenames: list,
            figsize: Tuple[int,int]=(10,10), colour: str=COPPER):
        """Plots a scatter plot of correlations for a single target.
        
        Args:
            target: The column name of correlations to get.
            filenames: The filename to save the plot to.
            figsize: The size in which to create the figure.
            colour: The colour the different cluster thresholds.
        
        """
        # Iterate through each correlation
        counter = 0
        for correlation in self.analyser.correlations:
            
            # Get the correlation for the target specifically
            target_corr = self.analyser.correlations[correlation][target]

            plt.figure(figsize=figsize)
            plt.scatter(range(len(target_corr)), target_corr, color=colour)

            # Set limits to be [-1, 1] with a bit of buffer
            plt.ylim([-1.05, 1.05])

            # Set xticks to the element names
            plt.xticks(range(len(target_corr.index)), target_corr.index, 
                    rotation=90)

            plt.title(f'{correlation} Targetting {target}')

            # Save the figure
            plt.savefig(filenames[counter])
            plt.close()

            counter += 1
            
    def plot_tf_model_losses(self, hist_path: str, filename: str):
        """Plots the training and validation loss of a neural network.

        Args:
            model_path: The path of where the saved model is.
            filename: The file to save the plot to.
        """
        model = pd.read_csv(hist_path)
        plt.plot(model['loss'], label='loss')
        plt.plot(model['val_loss'], label='validational loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid(True)
        plt.savefig(filename)
        plt.close()

    def plot_model_predictions(self, predictions: np.array, 
            actual: np.array, filename: str, figsize: Tuple[int,int]=(10,10), 
            label_font_size: int=16, title_font_size: int=24, rotation: int=0,
            colour: str=COPPER) -> None:
        """Plots predictions against their true values in scatterplot.
        
        Args:
            predictions: An array of predictions from tf.predict.
            actual: An array of true values, must be the same length as
              predictions (and correspond index to index).
            filename: File to save the visualisation to.
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the bars in the plot.
        """
        # Plot
        plt.figure(figsize=figsize)
        plt.scatter(predictions, actual, color=colour)

        # Labels
        plt.title('Comparison of Predictions vs Testing Set',
                fontsize=title_font_size)
        plt.xlabel('True Values', fontsize=label_font_size)
        plt.ylabel('Predictions', fontsize=label_font_size)

        # Plot a line for reference
        x = np.linspace(np.amin(actual), np.amax(actual), 1000)
        plt.plot(x, x, color='k')

        plt.savefig(filename)
        plt.close()

    def bar_tf_model_predictions(self, predictions: np.array,
            actual: np.array, filename: str) -> None:
        """Takes a model and produces a histogram of the errors.
        
        Args:
            predictions: An array of predictions from tf.predict.
            actual: An array of true values, must be the same length as
              predictions (and correspond index to index).
            filename: File to save the visualisation to.
        """
        error = predictions - actual.values.reshape(len(actual), 1)
        plt.hist(error)
        plt.savefig(filename)
        plt.close()

    def plot_adaboost_importances(self, filename: str, ordered: bool=True, 
            big_to_small: bool=True, horizontal: bool=True, 
            figsize: Tuple[int,int]=(10,10), label_font_size: int=16,
            title_font_size: int=24, rotation: int=0, 
            colour: str=COPPER) -> None:
        """
        Plots the importance of each feature in a pre-run AdaBoost. 
        
        Args:
            filename: The filename to save the plot to.
            ordered: Whether or not to sort the importances in ascending order
            big_to_small: If ordered is True, this indicates whether the plot
              should be in ascending or descending order.
            horizontal: If True, plots a horizontal bar graph. Otherwise,
              a normal bar graph (vertical) is created
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the bars in the plot.
        """

        # Log start

        # Check that there is an adaboost to get the importances of
        if self.analyser.adaboost is None:
            raise exceptions.ModelNotTrainedError('Adaboost')
        
        # Get the importances
        importances = self.analyser.adaboost.feature_importances_

        # Sort if necessary
        if ordered:
            if big_to_small:
                index_sorted = np.argsort(importances)[::-1]
                importances = np.sort(importances)[::-1]

            else:
                index_sorted = np.argsort(importances)
                importances = np.sort(importances)
        else:
            index_sorted = [i for i in range(len(importances))]
            
        if self.analyser.adaboost_subset_X is None:
            labels = [self.analyser.dataframe.columns[i] 
                    for i in index_sorted]
        else:
            labels = [self.analyser.adaboost_subset_X[i] for i in index_sorted]

        # Create figure and initialise with figure size
        plt.figure(figsize=figsize)

        if horizontal:
            # Plot the importances
            plt.barh(range(self.analyser.adaboost_num_predictors), 
                    importances, color=colour)

            # Set labels
            plt.yticks(ticks=range(self.analyser.adaboost_num_predictors), 
                    labels=labels, rotation=rotation, fontsize=label_font_size)

            plt.title("Importances AdaBoost Predicting {}".format(
                    self.analyser.ada_target_column), fontsize=title_font_size)

        else:
            # Plot the importances
            plt.bar(range(self.analyser.adaboost_num_predictors), importances, 
                    color=colour)

            # Set labels
            plt.xticks(range(self.analyser.adaboost_num_predictors), labels,
                    rotation=rotation, fontsize=label_font_size)

            plt.title("Importances AdaBoost Predicting {}".format(
                    self.analyser.ada_target_column), fontsize=title_font_size)


        # Save the figure
        plt.savefig(filename)

        plt.close()

    def plot_adaboost_importances_big_10(self, filename: str, ordered: bool = True,
                                  big_to_small: bool = True, horizontal: bool = True,
                                  figsize: Tuple[int, int] = (10, 10), label_font_size: int = 16,
                                  title_font_size: int = 24, rotation: int = 0,
                                  colour: str = COPPER) -> None:
        """
        Plots the importance of each feature in a pre-run AdaBoost.

        Args:
            filename: The filename to save the plot to.
            ordered: Whether or not to sort the importances in ascending order
            big_to_small: If ordered is True, this indicates whether the plot
              should be in ascending or descending order.
            horizontal: If True, plots a horizontal bar graph. Otherwise,
              a normal bar graph (vertical) is created
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the bars in the plot.
        """

        # Log start

        # Check that there is an adaboost to get the importances of
        if self.analyser.adaboost is None:
            raise exceptions.ModelNotTrainedError('Adaboost')

        # Get the importances
        importances = self.analyser.adaboost.feature_importances_

        # Sort if necessary
        if ordered:
            if big_to_small:
                index_sorted = np.argsort(importances)[::-1]
                importances = np.sort(importances)[::-1]

            else:
                index_sorted = np.argsort(importances)
                importances = np.sort(importances)
        else:
            index_sorted = [i for i in range(len(importances))]

        if self.analyser.adaboost_subset_X is None:
            labels = [self.analyser.dataframe.columns[i]
                      for i in index_sorted]
        else:
            labels = [self.analyser.adaboost_subset_X[i] for i in index_sorted]

        if len(importances) >= 10 and len(labels) >= 10:
            labels = labels[-10:]
            importances = importances[-10:]
        else:
            return False

        # Create figure and initialise with figure size
        plt.figure(figsize=figsize)

        if horizontal:
            # Plot the importances
            plt.barh(range(10),
                     importances, color=colour)

            # Set labels
            plt.yticks(ticks=range(10),
                       labels=labels, rotation=rotation, fontsize=label_font_size)

            plt.title("Biggest 10 Importances AdaBoost Predicting {}".format(
                self.analyser.ada_target_column), fontsize=title_font_size)

        else:
            # Plot the importances
            plt.bar(range(10), importances,
                    color=colour)

            # Set labels
            plt.xticks(range(10), labels,
                       rotation=rotation, fontsize=label_font_size)

            plt.title("Biggest 10 Importances AdaBoost Predicting {}".format(
                self.analyser.ada_target_column), fontsize=title_font_size)

        # Save the figure
        plt.savefig(filename)

        plt.close()

    def plot_adaboost_importances_small_10(self, filename: str, ordered: bool = True,
                                  big_to_small: bool = True, horizontal: bool = True,
                                  figsize: Tuple[int, int] = (10, 10), label_font_size: int = 16,
                                  title_font_size: int = 24, rotation: int = 0,
                                  colour: str = COPPER) -> None:
        """
        Plots the importance of each feature in a pre-run AdaBoost.

        Args:
            filename: The filename to save the plot to.
            ordered: Whether or not to sort the importances in ascending order
            big_to_small: If ordered is True, this indicates whether the plot
              should be in ascending or descending order.
            horizontal: If True, plots a horizontal bar graph. Otherwise,
              a normal bar graph (vertical) is created
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the bars in the plot.
        """

        # Log start

        # Check that there is an adaboost to get the importances of
        if self.analyser.adaboost is None:
            raise exceptions.ModelNotTrainedError('Adaboost')

        # Get the importances
        importances = self.analyser.adaboost.feature_importances_

        # Sort if necessary
        if ordered:
            if big_to_small:
                index_sorted = np.argsort(importances)[::-1]
                importances = np.sort(importances)[::-1]

            else:
                index_sorted = np.argsort(importances)
                importances = np.sort(importances)
        else:
            index_sorted = [i for i in range(len(importances))]

        if self.analyser.adaboost_subset_X is None:
            labels = [self.analyser.dataframe.columns[i]
                      for i in index_sorted]
        else:
            labels = [self.analyser.adaboost_subset_X[i] for i in index_sorted]


        if len(importances) >= 10 and len(labels) >= 10:
            labels = labels[:10]
            importances = importances[:10]
        else:
            return False

        # Create figure and initialise with figure size
        plt.figure(figsize=figsize)

        if horizontal:
            # Plot the importances
            plt.barh(range(10),
                     importances, color=colour)

            # Set labels
            plt.yticks(ticks=range(10),
                       labels=labels, rotation=rotation, fontsize=label_font_size)

            plt.title("Least 10 Importances AdaBoost Predicting {}".format(
                self.analyser.ada_target_column), fontsize=title_font_size)

        else:
            # Plot the importances
            plt.bar(range(10), importances,
                    color=colour)

            # Set labels
            plt.xticks(range(10), labels,
                       rotation=rotation, fontsize=label_font_size)

            plt.title("Least 10 Importances AdaBoost Predicting {}".format(
                self.analyser.ada_target_column), fontsize=title_font_size)

        # Save the figure
        plt.savefig(filename)

        plt.close()

    def plot_xgboost_importances(self, filename: str, ordered: bool=True, 
            big_to_small: bool=True, horizontal: bool=True, 
            figsize: Tuple[int,int]=(10,10), label_font_size: int=16,
            title_font_size: int=24, rotation: int=0, 
            colour: str=COPPER) -> None:
        """
        Plots the importance of each feature in a pre-run XGBoost. 
        
        Args:
            filename: The filename to save the plot to.
            ordered: Whether or not to sort the importances in ascending order
            big_to_small: If ordered is True, this indicates whether the plot
              should be in ascending or descending order.
            horizontal: If True, plots a horizontal bar graph. Otherwise,
              a normal bar graph (vertical) is created
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the bars in the plot.
        """

        # Log start

        # Check that there is an xgboost to get the importances of
        if self.analyser.xgboost is None:
            raise exceptions.ModelNotTrainedError('XGBoost')
        
        # Get the importances
        importances = self.analyser.xgboost.feature_importances_

        # Sort if necessary
        if ordered:
            if big_to_small:
                index_sorted = np.argsort(importances)[::-1]
                importances = np.sort(importances)[::-1]

            else:
                index_sorted = np.argsort(importances)
                importances = np.sort(importances)
        else:
            index_sorted = [i for i in range(len(importances))]
            
        if self.analyser.xgboost_subset_X is None:
            labels = [self.analyser.dataframe.columns[i] 
                    for i in index_sorted]
        else:
            labels = [self.analyser.xgboost_subset_X[i] for i in index_sorted]

        # Create figure and initialise with figure size
        plt.figure(figsize=figsize)

        if horizontal:
            # Plot the importances
            plt.barh(range(self.analyser.xgboost_num_predictors), 
                    importances, color=colour)

            # Set labels
            plt.yticks(ticks=range(self.analyser.xgboost_num_predictors), 
                    labels=labels, rotation=rotation, fontsize=label_font_size)

            plt.title("Importances XGBoost Predicting {}".format(
                    self.analyser.xgboost_target_column), 
                    fontsize=title_font_size)

        else:
            # Plot the importances
            plt.bar(range(self.analyser.xgboost_num_predictors), importances, 
                    color=colour)

            # Set labels
            plt.xticks(range(self.analyser.xgboost_num_predictors), labels,
                    rotation=rotation, fontsize=label_font_size)

            plt.title("Importances XGBoost Predicting {}".format(
                    self.analyser.xgboost_target_column), 
                    fontsize=title_font_size)


        # Save the figure
        plt.savefig(filename)

        plt.close()

    def plot_xgboost_importances_big_10(self, filename: str, ordered: bool = True,
                                 big_to_small: bool = True, horizontal: bool = True,
                                 figsize: Tuple[int, int] = (10, 10), label_font_size: int = 16,
                                 title_font_size: int = 24, rotation: int = 0,
                                 colour: str = COPPER) -> None:
        """
        Plots the importance of each feature in a pre-run XGBoost.

        Args:
            filename: The filename to save the plot to.
            ordered: Whether or not to sort the importances in ascending order
            big_to_small: If ordered is True, this indicates whether the plot
              should be in ascending or descending order.
            horizontal: If True, plots a horizontal bar graph. Otherwise,
              a normal bar graph (vertical) is created
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the bars in the plot.
        """

        # Log start

        # Check that there is an xgboost to get the importances of
        if self.analyser.xgboost is None:
            raise exceptions.ModelNotTrainedError('XGBoost')

        # Get the importances
        importances = self.analyser.xgboost.feature_importances_

        # Sort if necessary
        if ordered:
            if big_to_small:
                index_sorted = np.argsort(importances)[::-1]
                importances = np.sort(importances)[::-1]

            else:
                index_sorted = np.argsort(importances)
                importances = np.sort(importances)
        else:
            index_sorted = [i for i in range(len(importances))]

        if self.analyser.xgboost_subset_X is None:
            labels = [self.analyser.dataframe.columns[i]
                      for i in index_sorted]
        else:
            labels = [self.analyser.xgboost_subset_X[i] for i in index_sorted]

        if len(importances) >= 10 and len(labels) >= 10:
            labels = labels[-10:]
            importances = importances[-10:]
        else:
            return False

        # Create figure and initialise with figure size
        plt.figure(figsize=figsize)

        if horizontal:
            # Plot the importances
            plt.barh(range(10),
                     importances, color=colour)

            # Set labels
            plt.yticks(ticks=range(10),
                       labels=labels, rotation=rotation, fontsize=label_font_size)

            plt.title("Biggest 10 Importances XGBoost Predicting {}".format(
                self.analyser.xgboost_target_column),
                fontsize=title_font_size)

        else:
            # Plot the importances
            plt.bar(range(10), importances,
                    color=colour)

            # Set labels
            plt.xticks(range(10), labels,
                       rotation=rotation, fontsize=label_font_size)

            plt.title("Biggest 10 Importances XGBoost Predicting {}".format(
                self.analyser.xgboost_target_column),
                fontsize=title_font_size)

        # Save the figure
        plt.savefig(filename)

        plt.close()

    def plot_xgboost_importances_small_10(self, filename: str, ordered: bool = True,
                                 big_to_small: bool = True, horizontal: bool = True,
                                 figsize: Tuple[int, int] = (10, 10), label_font_size: int = 16,
                                 title_font_size: int = 24, rotation: int = 0,
                                 colour: str = COPPER) -> None:
        """
        Plots the importance of each feature in a pre-run XGBoost.

        Args:
            filename: The filename to save the plot to.
            ordered: Whether or not to sort the importances in ascending order
            big_to_small: If ordered is True, this indicates whether the plot
              should be in ascending or descending order.
            horizontal: If True, plots a horizontal bar graph. Otherwise,
              a normal bar graph (vertical) is created
            figsize: The size in which to create the figure.
            label_font_size: The font size of axis labels.
            title_font_size: The font size of title.
            rotation: The rotation of the tick labels.
            colour: The colour of the bars in the plot.
        """

        # Log start

        # Check that there is an xgboost to get the importances of
        if self.analyser.xgboost is None:
            raise exceptions.ModelNotTrainedError('XGBoost')

        # Get the importances
        importances = self.analyser.xgboost.feature_importances_

        # Sort if necessary
        if ordered:
            if big_to_small:
                index_sorted = np.argsort(importances)[::-1]
                importances = np.sort(importances)[::-1]

            else:
                index_sorted = np.argsort(importances)
                importances = np.sort(importances)
        else:
            index_sorted = [i for i in range(len(importances))]

        if self.analyser.xgboost_subset_X is None:
            labels = [self.analyser.dataframe.columns[i]
                      for i in index_sorted]
        else:
            labels = [self.analyser.xgboost_subset_X[i] for i in index_sorted]


        if len(importances) >= 10 and len(labels) >= 10:
            labels = labels[:10]
            importances = importances[:10]
        
        else:
            return False

        # Create figure and initialise with figure size
        plt.figure(figsize=figsize)

        if horizontal:
            # Plot the importances
            plt.barh(range(10),
                     importances, color=colour)

            # Set labels
            plt.yticks(ticks=range(10),
                       labels=labels, rotation=rotation, fontsize=label_font_size)

            plt.title("Least 10 Importances XGBoost Predicting {}".format(
                self.analyser.xgboost_target_column),
                fontsize=title_font_size)

        else:
            # Plot the importances
            plt.bar(range(10), importances,
                    color=colour)

            # Set labels
            plt.xticks(range(10), labels,
                       rotation=rotation, fontsize=label_font_size)

            plt.title("Least 10 Importances XGBoost Predicting {}".format(
                self.analyser.xgboost_target_column),
                fontsize=title_font_size)

        # Save the figure
        plt.savefig(filename)

        plt.close()
