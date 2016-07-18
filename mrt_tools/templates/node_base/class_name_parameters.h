#pragma once
#define STR(name) #name

#include <string>
#include <ros/node_handle.h>

namespace ${pkgname} {

struct ${ClassName}Parameters {

    static ${ClassName}Parameters& getInstance();

    void fromNodeHandle(const ros::NodeHandle&);

    int msg_queue_size;
    std::string verbosity;

    std::string publisher_msg_name;
    std::string subscriber_msg_name;

    std::string diag_pub_msg_name;              //@diagnostics@
    double diagnostic_updater_rate_tolerance;   //@diagnostics@
    std::string diagnostic_updater_name;        //@diagnostics@
    std::string diagnostic_updater_hardware_id; //@diagnostics@
    double diagnostic_updater_rate;             //@diagnostics@
    //@diagnostics@
    float dummy;

private:
    ${ClassName}Parameters(){};
};

} // namespace ${pkgname}
