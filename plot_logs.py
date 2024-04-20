import re
import matplotlib.pyplot as plt
import tld

total_responses_pattern = re.compile(r"Total responses: (\d+)")
mean_lscore_pattern = re.compile(
    r"Mean lscore value generated from last 100 responses: ([\d.]+)"
)
itemised_page_pattern = re.compile(r"Itemised page: (.+)")

total_responses = [0]
mean_lscores = [0]
itemised_pages = [0]
itemised_flds = [0]
itemisation_rates = [0]
unique_fld_rate = [0]

flds = set()

with open("logs/dvsvc-spiders.log", "r") as file:
    cur_itemised_count = 0
    cur_unique_fld_count = 0

    for line in file:
        match_total_responses = total_responses_pattern.search(line)
        if match_total_responses:
            total_responses.append(int(match_total_responses.group(1)))

            cur_responses = total_responses[-1] - total_responses[-2]

            itemised_pages.append(itemised_pages[-1] + cur_itemised_count)
            itemised_flds.append(itemised_flds[-1] + cur_unique_fld_count)

            itemisation_rates.append(cur_itemised_count / cur_responses)
            unique_fld_rate.append(cur_unique_fld_count / cur_responses)

            cur_itemised_count = 0
            cur_unique_fld_count = 0

        match_mean_lscore = mean_lscore_pattern.search(line)
        if match_mean_lscore:
            mean_lscores.append(float(match_mean_lscore.group(1)))

        match_itemised_page = itemised_page_pattern.search(line)
        if match_itemised_page:
            cur_itemised_count += 1

            fld = tld.get_tld(match_itemised_page.group(1), as_object=True).fld
            if fld not in flds:
                cur_unique_fld_count += 1
                flds.add(fld)


fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(12, 8))

ax1.plot(total_responses, itemised_flds)
ax1.set_xlabel("Total Responses")
ax1.set_ylabel("Itemised FLDs")
ax1.set_title("Itemised FLDs over Total Responses")
ax1.grid(True)

ax2.plot(total_responses, itemised_pages, color="red")
ax2.set_xlabel("Total Responses")
ax2.set_ylabel("Itemised Pages")
ax2.set_title("Itemised Pages over Total Responses")
ax2.grid(True)

ax3.plot(total_responses, unique_fld_rate)
ax3.set_xlabel("Total Responses")
ax3.set_ylabel("Discovery Rate")
ax3.set_title("Discovery Rate over Total Responses")
ax3.grid(True)

ax4.plot(total_responses, itemisation_rates, color="red")
ax4.set_xlabel("Total Responses")
ax4.set_ylabel("Itemisation Rate")
ax4.set_title("Itemisation Rate over Total Responses")
ax4.grid(True)

ax5.plot(total_responses, mean_lscores, color="green")
ax5.set_xlabel("Total Responses")
ax5.set_ylabel("Discovered lscore")
ax5.set_title("Discovered lscore over Total Responses")
ax5.grid(True)

# Adjust the spacing between subplots
plt.tight_layout()

# Display the plot
plt.show()
