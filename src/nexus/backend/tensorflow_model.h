#ifndef NEXUS_BACKEND_TENSORFLOW_MODEL_H_
#define NEXUS_BACKEND_TENSORFLOW_MODEL_H_

#if USE_TENSORFLOW == 1

#include "nexus/backend/model_ins.h"
// Tensorflow headers
#include "tensorflow/core/framework/allocator.h"
#include "tensorflow/core/public/session.h"

namespace tf = tensorflow;

namespace nexus {
namespace backend {

class TensorflowModel : public ModelInstance {
 public:
  TensorflowModel(int gpu_id, const std::string& model_name, uint32_t version, 
                  const std::string& type, uint32_t batch, uint32_t max_batch,
                  BlockPriorityQueue<Task>& task_queue, const YAML::Node& info);

  ~TensorflowModel();

  std::string framework() const final { return "tensorflow"; }

  std::string profile_id() const final;

 private:
  void InitBatchInputArray() final;

  void PreprocessImpl(std::shared_ptr<Task> task,
                      std::vector<ArrayPtr>* input_arrays) final;

  void ForwardImpl(BatchInput* batch_input, BatchOutput* batch_output) final;

  void PostprocessImpl(std::shared_ptr<Task> task, Output* output) final;

  void LoadClassnames(const std::string& filepath);

  void MarshalClassificationResult(
      const QueryProto& query, const float* prob, size_t nprobs,
      float threshold, QueryResultProto* result);
  
 private:
  tf::SessionOptions gpu_option_;
  tf::SessionOptions cpu_option_;
  std::unique_ptr<tf::Session> session_;
  int image_height_;
  int image_width_;
  size_t input_size_;
  std::string input_layer_;
  std::string output_layer_;
  std::vector<float> input_mean_;
  std::vector<float> input_std_;
  std::vector<std::string> classnames_;
  tf::Allocator* gpu_allocator_;
  std::unique_ptr<tf::Tensor> input_tensor_;
};

} // namespace backend
} // namespace nexus

#endif // USE_TENSORFLOW == 1

#endif // NEXUS_BACKEND_TENSORFLOW_MODEL_H_
