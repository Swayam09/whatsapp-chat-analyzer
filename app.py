import streamlit as st
import preprocessor, helper
import matplotlib.pyplot as plt
import seaborn as sns

st.sidebar.title('Whatsapp Chat Analyzer')

uploaded_file = st.sidebar.file_uploader("Choose a file")
if uploaded_file is not None:
    # To read file as bytes:
    bytes_data = uploaded_file.getvalue()
    data = bytes_data = bytes_data.decode('utf-8')

    df = preprocessor.preprocess(data)
    df = helper.normalize_omitted_messages(df)

    # Keep original df for stats
    df_full = df.copy()

    # Create a cleaned df for wordcloud / text analysis
    df_clean = helper.clean_chat_df(df, remove_omitted=True)  # removes <OMITTED> for text

    # st.dataframe(df)

    # fetch unique users
    user_list = df['user'].unique().tolist()
    if 'group_notification' in user_list:
        user_list.remove('group_notification')

    user_list.sort()
    user_list.insert(0, 'overall')
    selected_user = st.sidebar.selectbox('Choose a user', user_list)

    if st.sidebar.button('Show Analysis'):
        # stats area
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df_full)

        st.title("Top Stats")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.header('Total Messages')
            st.title(num_messages)

        with col2:
            st.header('Total Words')
            st.title(words)

        with col3:
            st.header('Total Media')
            st.title(num_media_messages)

        with col4:
            st.header('Total Links')
            st.title(num_links)


        # monthly timeline
        st.title('Monthly Timeline')
        timeline = helper.monthly_timeline(selected_user, df_full)
        fig, ax = plt.subplots()
        ax.plot(timeline['time'], timeline['message'], color='blue')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # daily timeline
        st.title('Daily Timeline')
        daily_timeline = helper.daily_timeline(selected_user, df_full)
        fig, ax = plt.subplots()
        ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='red')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # activity map
        st.title('Activity Map')
        col1, col2 = st.columns(2)

        with col1:
            st.header('Most Busy Day')
            busy_day = helper.week_activity_map(selected_user, df_full)
            fig, ax = plt.subplots()
            ax.bar(busy_day.index, busy_day.values, color='orange')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        with col2:
            st.header('Most Busy Month')
            busy_month = helper.month_activity_map(selected_user, df_full)
            fig, ax = plt.subplots()
            ax.bar(busy_month.index, busy_month.values, color='teal')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        st.title('Weekly Activity Map')
        user_heatmap = helper.activity_heatmap(selected_user, df_full)
        fig, ax = plt.subplots()
        ax = sns.heatmap(user_heatmap, cmap='YlGnBu', fmt='g')
        st.pyplot(fig)


        # find the busiest users in the group (at grp level)
        if selected_user == 'overall':
            st.title('Most Busy Users')
            x, new_df = helper.most_busy_users(df)
            fig, ax = plt.subplots()

            col1, col2 = st.columns(2)

            with col1:
                ax.bar(x.index, x.values, color='lightcoral')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)

            with col2:
                st.dataframe(new_df)

        # wordcloud
        st.title("WordCloud")
        wc = helper.create_wordcloud(selected_user, df_clean)

        if wc is None:
            st.info("No text available to generate wordcloud for this selection.")
        else:
            fig, ax = plt.subplots()
            ax.imshow(wc.to_array(), interpolation='bilinear')  # <-- key change
            ax.axis("off")
            st.pyplot(fig)

        # most common words
        st.title("Most Common Words")

        common_df = helper.most_common_words(selected_user, df_clean, top_n=20)

        if common_df.empty:
            st.info("No words available to show.")
        else:
            fig, ax = plt.subplots()
            ax.barh(common_df["word"][::-1], common_df["count"][::-1], color='mediumslateblue')
            ax.set_xlabel("Frequency")
            ax.set_ylabel("Word")
            st.pyplot(fig)

        # emoji analysis
        emoji_df = helper.emoji_helper(selected_user, df_full)
        st.title("Emoji Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(emoji_df)
        with col2:
            top = emoji_df.head(5)  # only top 10 emojis
            fig, ax = plt.subplots()
            ax.pie(
                top["count"],
                labels=top["emoji"],
                autopct="%1.1f%%",
                startangle=90
            )
            ax.axis("equal")
            st.pyplot(fig)
